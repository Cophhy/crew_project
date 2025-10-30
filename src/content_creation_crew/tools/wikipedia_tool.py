# src/content_creation_crew/tools/wikipedia_tool.py
from __future__ import annotations

import json
import os
from typing import Optional, Type, List, Dict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

WIKI_API = "https://{lang}.wikipedia.org/w/api.php"

# ---------------------------
# HTTP Session com User-Agent e Retry
# ---------------------------

def _build_session() -> requests.Session:
    app_name = os.getenv("APP_NAME", "crew_project")
    app_ver = os.getenv("APP_VERSION", "0.1")
    contact = os.getenv("WIKI_CONTACT", "dev@example.com")

    s = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update(
        {
            # Requisito da Wikimedia: User-Agent identificável c/ contato
            # https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy
            "User-Agent": f"{app_name}/{app_ver} (+https://github.com/Cophhy/crew_project; contact={contact})",
            "Accept": "application/json",
        }
    )
    return s

SESSION = _build_session()

# ---------------------------
# Schemas (Pydantic v2)
# ---------------------------

class WikipediaSearchInput(BaseModel):
    query: str = Field(..., description="Termo de busca")
    lang: str = Field("en", description="Idioma da Wikipédia, ex.: en, pt, es")
    limit: int = Field(5, ge=1, le=20, description="Quantidade de resultados (1-20)")

class WikipediaFetchInput(BaseModel):
    title: str = Field(..., description="Título exato do artigo")
    lang: str = Field("en", description="Idioma da Wikipédia, ex.: en, pt, es")
    section: Optional[str] = Field(
        None, description="(Opcional) seção; se vazio, retorna o lead"
    )

# ---------------------------
# Helpers
# ---------------------------

def _assert_ok(resp: requests.Response, where: str) -> Dict:
    if resp.status_code >= 400:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise requests.HTTPError(f"{resp.status_code} Error on {where}: {detail}")
    return resp.json()

def _query_extracts_info(lang: str, titles: List[str]) -> List[Dict]:
    """
    Retorna para cada título:
      - title
      - extract (somente lead, plaintext)
      - canonicalurl (URL canônica p/ citação)
    """
    params = {
        "action": "query",
        "prop": "extracts|info",
        "exintro": 1,
        "explaintext": 1,
        "inprop": "url",
        "format": "json",
        "formatversion": 2,
        "titles": "|".join(titles),
        "utf8": 1,
    }
    r = SESSION.get(WIKI_API.format(lang=lang), params=params, timeout=30)
    data = _assert_ok(r, "extracts|info")
    pages = data.get("query", {}).get("pages", [])
    out = []
    for p in pages:
        out.append(
            {
                "title": p.get("title"),
                "extract": p.get("extract", ""),
                "canonical_url": p.get("fullurl"),  # URL canônica
            }
        )
    return out

# ---------------------------
# Ferramentas CrewAI
# ---------------------------

class WikipediaSearchTool(BaseTool):
    """Busca títulos no Wikipedia e devolve {title, extract, canonical_url}."""
    name: str = "wikipedia_search"
    description: str = "Busca títulos e retorna resumo limpo + URL canônica."
    args_schema: Type[WikipediaSearchInput] = WikipediaSearchInput

    def _run(self, **kwargs) -> str:
        args = WikipediaSearchInput(**kwargs)

        # 1) Buscar títulos
        params = {
            "action": "query",
            "list": "search",
            "srsearch": args.query,
            "srlimit": args.limit,
            "format": "json",
            "formatversion": 2,
            "utf8": 1,
        }
        r = SESSION.get(WIKI_API.format(lang=args.lang), params=params, timeout=30)
        data = _assert_ok(r, "wikipedia_search:list=search")

        titles = [it["title"] for it in data.get("query", {}).get("search", [])]
        if not titles:
            return json.dumps([], ensure_ascii=False)

        # 2) Enriquecer com extract + canonical_url
        enriched = _query_extracts_info(args.lang, titles)
        return json.dumps(enriched, ensure_ascii=False)

    async def _arun(self, **kwargs) -> str:
        return self._run(**kwargs)

class WikipediaFetchTool(BaseTool):
    """
    Retorna lead 'limpo' e URL canônica de um artigo.
    Use 'section' se precisar de uma seção específica (quando None, pega só o lead).
    """
    name: str = "wikipedia_fetch"
    description: str = "Busca o resumo (lead) limpo + URL canônica de um artigo do Wikipedia."
    args_schema: Type[WikipediaFetchInput] = WikipediaFetchInput

    def _run(self, **kwargs) -> str:
        args = WikipediaFetchInput(**kwargs)

        # Se section==None → só o lead via extracts|info (limpo)
        if not args.section:
            enriched = _query_extracts_info(args.lang, [args.title])
            return json.dumps(enriched[0] if enriched else {}, ensure_ascii=False)

        # Se section foi pedida: ainda dá para usar 'parse' só na seção,
        # mas manteremos texto; URL canônica vem via chamada extra de info.
        params = {
            "action": "parse",
            "page": args.title,
            "prop": "wikitext",
            "section": args.section,
            "format": "json",
            "formatversion": 2,
            "utf8": 1,
        }
        pr = SESSION.get(WIKI_API.format(lang=args.lang), params=params, timeout=30)
        pdata = _assert_ok(pr, "wikipedia_fetch:parse(section)")
        # wikitext simples da seção pedida
        section_text = pdata.get("parse", {}).get("wikitext", "")

        info = _query_extracts_info(args.lang, [args.title])
        canonical = info[0]["canonical_url"] if info else None

        return json.dumps(
            {"title": args.title, "section": args.section, "text": section_text, "canonical_url": canonical},
            ensure_ascii=False,
        )

    async def _arun(self, **kwargs) -> str:
        return self._run(**kwargs)

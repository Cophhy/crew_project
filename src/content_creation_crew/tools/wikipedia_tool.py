from __future__ import annotations

import os
import json
import re
import time
import html
from pydantic import BaseModel, Field, PrivateAttr
from typing import Optional, Dict, Any, Tuple, Type
from urllib.parse import urlparse, unquote

try:
    # Carrega .env se disponível
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


WIKI_API = "https://{lang}.wikipedia.org/w/api.php"
APP_UA_NAME = os.getenv("APP_UA_NAME", "ContentCreationCrew/0.1")
WIKI_CONTACT_RAW = os.getenv("WIKI_CONTACT", "https://github.com/Cophhy/crew_project")

def _format_contact(contact: str) -> str:
    """Formata contato para User-Agent. Se for e-mail, prefixa com mailto:"""
    contact = (contact or "").strip()
    if "@" in contact and not contact.startswith("mailto:"):
        return f"mailto:{contact}"
    return contact

WIKI_CONTACT = _format_contact(WIKI_CONTACT_RAW)

def _maybe_parse_json(payload: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(payload)
    except Exception:
        return None

def _build_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({
        "User-Agent": f"{APP_UA_NAME} (+{WIKI_CONTACT})",
        "Accept": "application/json",
    })
    return s

def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return text.strip()

# Cria uma única sessão por módulo
_SHARED_SESSION = _build_session()


class WikipediaSearchInput(BaseModel):
    query: str = Field(..., description="Plain text query or JSON string.")

class WikipediaSearchTool(BaseTool):
    """Search Wikipedia strictly via MediaWiki API (no external links)."""

    # Campos Pydantic (configuráveis por instância)
    lang: str = "en"
    max_chars: int = 1800
    max_searches: int = 3  # Limite o número de pesquisas realizadas

    # Metadados do Tool
    name: str = "wikipedia_search"
    description: str = (
        "Search Wikipedia using ONLY the official MediaWiki API. "
        "Accepts either a plain query string, or a JSON string like "
        '{"query": "...", "lang": "en", "limit": 5}. '
        "Returns titles, snippets, and Wikipedia URLs."
    )

    args_schema: type[BaseModel] = WikipediaSearchInput 
    _session: ClassVar[requests.Session] = _SHARED_SESSION

    def _call_api(self, lang: str, params: Dict[str, Any]) -> requests.Response:
        """Chama a API da Wikipedia e retorna a resposta."""
        params = {"origin": "*", **params}
        url = WIKI_API.format(lang=lang)
        r = self._session.get(url, params=params, timeout=20)
        if r.status_code == 403:
            time.sleep(0.8)
            r = self._session.get(url, params=params, timeout=20)
        r.raise_for_status()
        return r

    def _run(self, query: str) -> str:
        """Executa a pesquisa na Wikipedia com base na consulta fornecida, limitando o número de pesquisas."""

        # Variável para controlar o número de pesquisas realizadas
        search_count = 0
        max_searches = self.max_searches

        data = _maybe_parse_json(query)
        if isinstance(data, dict):
            q = data.get("query") or data.get("q") or ""
            lang = (data.get("lang") or self.lang or "en").strip() or "en"
            limit = int(data.get("limit") or 5)
        else:
            q = query
            lang = self.lang or "en"
            limit = 5

        if not q or not isinstance(q, str):
            return "No Wikipedia results for this query."

        # Limita o número de pesquisas
        while search_count < max_searches:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": q,
                "srlimit": max(1, min(limit, 20)),
                "format": "json",
                "utf8": 1,
            }

            r = self._call_api(lang, params)
            results = r.json().get("query", {}).get("search", [])

            if results:
                lines = []
                for i, it in enumerate(results):
                    title = it.get("title", "")
                    url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
                    snippet = it.get("snippet", "")
                    snippet = snippet.replace('<span class="searchmatch">', "").replace("</span>", "")
                    snippet = _strip_html(snippet)
                    if len(snippet) > self.max_chars:
                        snippet = snippet[: self.max_chars].rstrip() + "..."
                    lines.append(f"- {i+1}. {title} – {url} — {snippet}")

                return "Wikipedia results (API)\n" + "\n".join(lines)

            else:
                # Caso não haja resultados, incrementa o contador e tenta novamente
                search_count += 1  
                time.sleep(0.5)  # Espera um pouco antes de tentar novamente

        # Caso o limite de pesquisas seja atingido, retorna uma mensagem
        return "No Wikipedia results for this query after multiple attempts."

    async def _arun(self, *_args, **_kwargs) -> str:
        """Método assíncrono não implementado para esta ferramenta."""
        raise NotImplementedError("WikipediaSearchTool does not support async.")

class WikipediaFetchInput(BaseModel):
    #title_or_json ou campos separados
    title_or_json: Optional[str] = Field(
        default=None,
        description="Plain title string or JSON string. Can be omitted if using 'title'/'url'."
    )
    title: Optional[str] = Field(default=None, description="Wikipedia page title")
    lang: Optional[str] = Field(default=None, description="Language code, e.g. 'en'")
    section: Optional[str] = Field(default=None, description="Section name to fetch")
    url: Optional[str] = Field(default=None, description="Full Wikipedia /wiki/ URL, may include #anchor")

class WikipediaFetchTool(BaseTool):
    """Fetch plaintext extract (or a section) from a Wikipedia page via MediaWiki API.
       Accepts page title, JSON string, OR a full /wiki/ URL (with #anchor).
    """

    lang: str = "en"
    max_chars: int = 6000

    name: str = "wikipedia_fetch"
    description: str = (
        "Fetch plaintext from a Wikipedia page using the MediaWiki API. "
        "You can pass: (1) title_or_json as a string, (2) separate fields like "
        '{"title":"...","lang":"en","section":"History"}, or (3) "url": '
        "https://en.wikipedia.org/wiki/String_theory#Overview ."
    )

    args_schema: type[BaseModel] = WikipediaFetchInput
    _session: ClassVar[requests.Session] = _SHARED_SESSION

    def _call_api(self, lang: str, params: Dict[str, Any]) -> requests.Response:
        params = {"origin": "*", **params}
        url = WIKI_API.format(lang=lang)
        r = self._session.get(url, params=params, timeout=20)
        if r.status_code == 403:
            time.sleep(0.8)
            r = self._session.get(url, params=params, timeout=20)
        r.raise_for_status()
        return r

    @staticmethod
    def _is_wiki_url(s: str) -> bool:
        try:
            p = urlparse(s)
            return bool(p.scheme and p.netloc) and "/wiki/" in p.path
        except Exception:
            return False

    @staticmethod
    def _clean_section_name(s: str) -> str:
        s = s.strip().strip("#").strip("}").strip()
        s = unquote(s)
        s = s.replace("_", " ")
        return s

    @staticmethod
    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", s.lower().strip())

    def _extract_title_and_section_from_url(self, url: str) -> Tuple[Optional[str], str, Optional[str]]:
        p = urlparse(url)
        host = (p.netloc or "").lower()
        lang = None
        if host.endswith(".wikipedia.org"):
            lang = host.split(".wikipedia.org")[0] or None
        path = p.path or ""
        try:
            idx = path.index("/wiki/")
            raw_title = path[idx + len("/wiki/") :]
        except ValueError:
            raw_title = ""
        title = unquote(raw_title).replace("_", " ").strip()
        section = self._clean_section_name(p.fragment) if p.fragment else None
        return (lang, title, section)

    def _run(
        self,
        title_or_json: Optional[str] = None,
        title: Optional[str] = None,
        lang: Optional[str] = None,
        section: Optional[str] = None,
        url: Optional[str] = None,
    ) -> str:
        effective_lang = (lang or self.lang or "en").strip() or "en"

        # Se URL extrai titulo
        if url and self._is_wiki_url(url):
            url_lang, url_title, url_section = self._extract_title_and_section_from_url(url)
            if url_lang:
                effective_lang = url_lang
            title = url_title or title
            section = url_section or section

        # se title_or_json parsear como JSON; senao usar como titulo simples
        if title_or_json:
            parsed = _maybe_parse_json(title_or_json)
            if isinstance(parsed, dict):
                title = parsed.get("title") or title
                effective_lang = (parsed.get("lang") or effective_lang).strip() or "en"
                sec = parsed.get("section")
                if isinstance(sec, str):
                    section = self._clean_section_name(sec)
            else:
                # era um título simples
                title = title or title_or_json.strip()

        if not title:
            return "Please provide a valid Wikipedia page title or URL."

        if section:
            target = self._norm(self._clean_section_name(str(section)))
            sec_params = {
                "action": "parse",
                "page": title,
                "prop": "sections",
                "format": "json",
                "utf8": 1
            }
            rs = self._call_api(effective_lang, sec_params)
            sections = rs.json().get("parse", {}).get("sections", [])

            idx = None
            for s in sections:
                line = s.get("line", "")
                if not line:
                    continue
                nline = self._norm(self._clean_section_name(line))
                if nline == target or nline.startswith(target):
                    idx = s.get("index")
                    break
            if idx is None:
                alt = re.sub(r"[\(\)]", "", target)
                for s in sections:
                    nline = self._norm(self._clean_section_name(s.get("line", "")))
                    if nline == alt or nline.startswith(alt):
                        idx = s.get("index")
                        break
            if idx is None:
                return f"Section '{section}' not found in '{title}' ({effective_lang})."

            params = {
                "action": "parse",
                "page": title,
                "prop": "text",
                "section": idx,
                "format": "json",
                "utf8": 1
            }
            r = self._call_api(effective_lang, params)
            html_text = r.json().get("parse", {}).get("text", {}).get("*", "")
            text = _strip_html(html_text)
            if not text:
                return f"Section '{section}' found but empty for '{title}' ({effective_lang})."
            if len(text) > self.max_chars:
                text = text[: self.max_chars].rstrip() + "..."
            return f"=== {title} — Section: {section} ===\n{text}"

        params = {
            "action": "query",
            "prop": "extracts",
            "titles": title,
            "explaintext": 1,
            "format": "json",
            "utf8": 1
        }
        r = self._call_api(effective_lang, params)
        pages = r.json().get("query", {}).get("pages", {})
        if not pages:
            return f"Page '{title}' not found on Wikipedia ({effective_lang})."

        page = next(iter(pages.values()))
        extract = (page.get("extract") or "").strip()
        if not extract:
            return f"Page '{title}' found, but no extract available ({effective_lang})."
        if len(extract) > self.max_chars:
            extract = extract[: self.max_chars].rstrip() + "..."
        return f"=== {title} (Wikipedia {effective_lang}) ===\n{extract}"

    async def _arun(self, *_args, **_kwargs) -> str:
        raise NotImplementedError("WikipediaFetchTool does not support async.")

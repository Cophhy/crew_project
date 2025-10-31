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
    from dotenv import load_dotenv
    load_dotenv()  # Carrega o arquivo .env
except Exception:
    pass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pydantic import BaseModel, Field
from crewai.tools import BaseTool  

# API do Wikipedia
WIKI_API = "https://{lang}.wikipedia.org/w/api.php"

# Define o nome do agente de usuário e o contato para o cabeçalho HTTP
APP_UA_NAME = os.getenv("APP_UA_NAME", "ContentCreationCrew/0.1")
WIKI_CONTACT_RAW = os.getenv("WIKI_CONTACT", "https://github.com/Cophhy/crew_project")

def _format_contact(contact: str) -> str:
    """
    Formata o contato para o User-Agent.
    Se o contato for um e-mail, ele será prefixado com 'mailto:'.

    Args:
    - contact: O contato fornecido, geralmente um e-mail ou URL.

    Retorna:
    - O contato formatado com o prefixo adequado (caso seja um e-mail).
    """
    contact = (contact or "").strip()  # Remove espaços extras do contato
    if "@" in contact and not contact.startswith("mailto:"):
        return f"mailto:{contact}"  # Se for e-mail, prefixa com "mailto:"
    return contact  # Caso contrário, retorna o contato como está

# Formata o contato do usuário para o cabeçalho do User-Agent
WIKI_CONTACT = _format_contact(WIKI_CONTACT_RAW)

def _maybe_parse_json(payload: str) -> Optional[Dict[str, Any]]:
    """
    Tenta parsear o payload como JSON.

    """
    try:
        return json.loads(payload)  
    except Exception:
        return None  

def _build_session() -> requests.Session:
    """
    Cria uma sessão HTTP configurada para realizar requisições com retry em caso de falhas.

    """
    s = requests.Session()  # nova sessão HTTP
    retry = Retry(
        total=3,  # Tenta 3 vezes
        backoff_factor=0.6,  # Intervalo entre as tentativas
        status_forcelist=[429, 500, 502, 503, 504],  # Lista de erros para retry
        allowed_methods=frozenset(["GET"]),  # apenas metodos GET são configurados para retry
        raise_on_status=False,  # nao lança excecão automaticamente
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))  # adapter para retries
    s.headers.update({
        "User-Agent": f"{APP_UA_NAME} (+{WIKI_CONTACT})", 
        "Accept": "application/json",  # Espera resposta em formato JSON
    })
    return s  # Retorna a sessão configurada

def _strip_html(text: str) -> str:
    """
    Remove tags HTML do texto e realiza a decodificação de caracteres especiais.

    """
    text = re.sub(r"<[^>]+>", "", text)  # Remove as tags HTML
    text = html.unescape(text)  
    return text.strip()  

#uma unica sessão compartilhada
_SHARED_SESSION = _build_session()


class WikipediaSearchInput(BaseModel):
    """
    Esquema de entrada para a ferramenta de pesquisa no Wikipedia
    Define o formato dos dados para a ferramenta de pesquisa
    """
    query: str = Field(..., description="Texto simples de pesquisa ou string JSON.")

class WikipediaSearchTool(BaseTool):
    """
    pesquisa no Wikipedia utilizando a API MediaWiki
    """
    lang: str = "en"  
    max_chars: int = 1800  

    # Metadados da ferramenta
    name: str = "wikipedia_search"
    description: str = (
        "Realiza pesquisa no Wikipedia usando apenas a API oficial do MediaWiki. "
        "Aceita uma string de consulta simples ou uma string JSON como: "
        '{"query": "...", "lang": "en", "limit": 5}. '
        "Retorna títulos, trechos e URLs do Wikipedia."
    )

    args_schema: Type[BaseModel] = WikipediaSearchInput  # esquema de entrada utilizando Pydantic
    _session: ClassVar[requests.Session] = _SHARED_SESSION  # HTTP compartilhada

    def _call_api(self, lang: str, params: Dict[str, Any]) -> requests.Response:
        """
        Chama a API do Wikipedia com os parâmetros fornecidos.

        """
        params = {"origin": "*", **params}  # Adiciona o parametro de origem para CORS
        url = WIKI_API.format(lang=lang)  # URL da API do Wikipedia
        r = self._session.get(url, params=params, timeout=20)  
        if r.status_code == 403:  
            time.sleep(0.8)
            r = self._session.get(url, params=params, timeout=20)
        r.raise_for_status() 
        return r  

    def _run(self, query: str) -> str:
        """
        Executa a pesquisa no Wikipedia usando os dados fornecidos.
   
        """
        data = _maybe_parse_json(query)  #tenta parsear a consulta como JSON
        if isinstance(data, dict):
            # Se JSON, usa os parâmetros de query idioma e limite da pesquisa
            q = data.get("query") or data.get("q") or ""
            lang = (data.get("lang") or self.lang or "en").strip() or "en"
            limit = int(data.get("limit") or 5)
        else:
            q = query
            lang = self.lang or "en"
            limit = 5

        if not q or not isinstance(q, str):
            return "No Wikipedia results for this query."  

        params = {
            "action": "query",
            "list": "search",
            "srsearch": q,  # Parsmetro da pesquisa
            "srlimit": max(1, min(limit, 20)),  # Limita o numero de resultados
            "format": "json",  # Formato da resposta
            "utf8": 1,  # Codificação UTF-8
        }

        r = self._call_api(lang, params)  # API do Wikipedia com os parâmetros
        results = r.json().get("query", {}).get("search", [])  

        if not results:
            return "No Wikipedia results for this query." 

        # Formata os resultados como uma lista
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

        return "Wikipedia results (API)\n" + "\n".join(lines)  # Retorna os resultados como uma string

    async def _arun(self, *_args, **_kwargs) -> str:
        """
        Método assíncrono não implementado para esta ferramenta.
        """
        raise NotImplementedError("WikipediaSearchTool does not support async.")

class WikipediaFetchInput(BaseModel):
    # Aceita E/OU: title_or_json (string), ou campos separados
    title_or_json: Optional[str] = Field(
        default=None,
        description="String com título ou JSON. Pode ser omitido se usar 'title'/'url'."
    )
    title: Optional[str] = Field(default=None, description="Título da página do Wikipedia")
    lang: Optional[str] = Field(default=None, description="Código de idioma, ex: 'en'")
    section: Optional[str] = Field(default=None, description="Nome da seção a ser buscada")
    url: Optional[str] = Field(default=None, description="URL completa do Wikipedia /wiki/, pode incluir #âncora")

class WikipediaFetchTool(BaseTool):
    """
    Ferramenta para buscar o texto completo ou uma seção específica
    Aceita título da página, string JSON ou URL completa
    """
    # Campos Pydantic
    lang: str = "en"  # Define o idioma (padrão é inglês)
    max_chars: int = 6000  # Número máximo de caracteres

    # Metadados da ferramenta
    name: str = "wikipedia_fetch"
    description: str = (
        "Busca o texto completo ou uma seção de uma página do Wikipedia usando a API MediaWiki. "
        "Você pode passar: (1) título ou JSON como string, (2) campos separados como "
        '{"title":"...","lang":"en","section":"History"}, ou (3) "url": '
        "https://en.wikipedia.org/wiki/String_theory#Overview ."
    )

    args_schema: type[BaseModel] = WikipediaFetchInput  # Esquema de entrada utilizando Pydantic
    _session: ClassVar[requests.Session] = _SHARED_SESSION  # Sessão HTTP compartilhada

    def _call_api(self, lang: str, params: Dict[str, Any]) -> requests.Response:
        """
        Chama a API MediaWiki com os parâmetros fornecidos e retorna a resposta.

        """
        params = {"origin": "*", **params}  # Adiciona o parâmetro de origem para CORS
        url = WIKI_API.format(lang=lang)  # Formata a URL da API do Wikipedia
        r = self._session.get(url, params=params, timeout=20)  # Faz a requisição
        if r.status_code == 403:  # Se o status for 403 (Forbidden), tenta novamente após 0.8 segundos
            time.sleep(0.8)
            r = self._session.get(url, params=params, timeout=20)
        r.raise_for_status()  # Lança exceção se o código de status for um erro
        return r  # Retorna a resposta da API


    @staticmethod
    def _is_wiki_url(s: str) -> bool:
        """
        Verifica se a string fornecida e valida e do Wikipedia
        """
        try:
            p = urlparse(s)
            return bool(p.scheme and p.netloc) and "/wiki/" in p.path
        except Exception:
            return False

    @staticmethod
    def _clean_section_name(s: str) -> str:
        """
        Limpa o nome, removendo caracteres especiais e espaços extras
        """
        s = s.strip().strip("#").strip("}").strip()
        s = unquote(s)  # Decodifica a URL
        s = s.replace("_", " ")  # Substitui underscores por espacos
        return s

    @staticmethod
    def _norm(s: str) -> str:
        """
        Normaliza a string para um formato padrão (minúsculas e espaços simples).
        """
        return re.sub(r"\s+", " ", s.lower().strip())

    def _extract_title_and_section_from_url(self, url: str) -> Tuple[Optional[str], str, Optional[str]]:
        """
        Extrai o titulo e a seção de uma URL do Wikipedia.
        """
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
        """
        Executa a busca ou a extração de texto a partir de uma página ou seção do Wikipedia.

        """
        effective_lang = (lang or self.lang or "en").strip() or "en"

        # Se URL, extrai titulo/ancora
        if url and self._is_wiki_url(url):
            url_lang, url_title, url_section = self._extract_title_and_section_from_url(url)
            if url_lang:
                effective_lang = url_lang
            title = url_title or title
            section = url_section or section

        # Se title_or_json (string), tenta parsear como JSON; senão usa como título simples
        if title_or_json:
            parsed = _maybe_parse_json(title_or_json)
            if isinstance(parsed, dict):
                title = parsed.get("title") or title
                effective_lang = (parsed.get("lang") or effective_lang).strip() or "en"
                sec = parsed.get("section")
                if isinstance(sec, str):
                    section = self._clean_section_name(sec)
            else:
                # Era um título simples
                title = title or title_or_json.strip()

        if not title:
            return "Please provide a valid Wikipedia page title or URL."

        # Seção específica?
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
                # remove parênteses
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

        #Página inteira (extract)
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
        """
        Método assíncrono não implementado para esta ferramenta.
        """
        raise NotImplementedError("WikipediaFetchTool does not support async.")

# src/content_creation_crew/tools/wikipedia_tool.py
from __future__ import annotations

# --- stdlib ---
import os
import json
import re
import time
import html
from typing import Optional, Dict, Any, Tuple, ClassVar, Type  # <- ClassVar e Type
from urllib.parse import urlparse, unquote

# --- third-party ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pydantic import BaseModel, Field  # <- manter um único import

# --- crewai ---
from crewai.tools import BaseTool

# ==========================
# Config & Utils
# ==========================

WIKI_API = "https://{lang}.wikipedia.org/w/api.php"

APP_UA_NAME = os.getenv("APP_UA_NAME", "ContentCreationCrew/0.1")
WIKI_CONTACT_RAW = os.getenv("WIKI_CONTACT", "https://github.com/Cophhy/crew_project")

def _format_contact(contact: str) -> str:
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
        allowed_methods=frozenset({"GET"}),  # <- ok para urllib3 1.26+ / 2.x
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

_SHARED_SESSION = _build_session()

# ==========================
# Search Tool
# ==========================

class WikipediaSearchInput(BaseModel):
    query: str = Field(..., description="Plain text query or JSON string.")

class WikipediaSearchTool(BaseTool):
    """Search Wikipedia strictly via MediaWiki API (no external links)."""

    # Config por instância
    lang: str = "en"
    max_chars: int = 1800

    # Metadados do Tool
    name: str = "wikipedia_search"
    description: str = (
        "Search Wikipedia using ONLY the official MediaWiki API. "
        "Accepts either a plain query string, or a JSON string like "
        '{"query": "...", "lang": "en", "limit": 5}. '
        "Returns titles, snippets, and Wikipedia URLs."
    )

    args_schema: Type[BaseModel] = WikipediaSearchInput  # <- Type[BaseModel]
    _session: ClassVar[requests.Session] = _SHARED_SESSION  # <- ClassVar importado

    def _call_api(self, lang: str, params: Dict[str, Any]) -> requests.Response:
        params = {"origin": "*", **params}
        url = WIKI_API.format(lang=lang)
        r = self._session.get(url, params=params, timeout=20)
        if r.status_code == 403:
            time.sleep(0.8)
            r = self._session.get(url, params=params, timeout=20)
        r.raise_for_status()
        return r

    def _run(self, query: str) -> str:
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

        params = {
            "action": "query",
            "list": "search",
            "srsearch": q,                    # MediaWiki API param
            "srlimit": max(1, min(limit, 20)),  # MediaWiki API param
            "format": "json",
            "utf8": 1,
        }

        r = self._call_api(lang, params)
        results = r.json().get("query", {}).get("search", [])

        if not results:
            return "No Wikipedia results for this query."

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

    async def _arun(self, *_args, **_kwargs) -> str:
        raise NotImplementedError("WikipediaSearchTool does not support async.")

# ==========================
# Fetch Tool
# ==========================

class WikipediaFetchInput(BaseModel):
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

    args_schema: Type[BaseModel] = WikipediaFetchInput  # <- Type[BaseModel]
    _session: ClassVar[requests.Session] = _SHARED_SESSION

    # ---------- HTTP ----------
    def _call_api(self, lang: str, params: Dict[str, Any]) -> requests.Response:
        params = {"origin": "*", **params}
        url = WIKI_API.format(lang=lang)
        r = self._session.get(url, params=params, timeout=20)
        if r.status_code == 403:
            time.sleep(0.8)
            r = self._session.get(url, params=params, timeout=20)
        r.raise_for_status()
        return r

    # ---------- helpers ----------
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

    # ---------- implementação principal ----------
    def _run(
        self,
        title_or_json: Optional[str] = None,
        title: Optional[str] = None,
        lang: Optional[str] = None,
        section: Optional[str] = None,
        url: Optional[str] = None,
    ) -> str:
        effective_lang = (lang or self.lang or "en").strip() or "en"

        # 1) URL com possível #anchor
        if url and self._is_wiki_url(url):
            url_lang, url_title, url_section = self._extract_title_and_section_from_url(url)
            if url_lang:
                effective_lang = url_lang
            title = url_title or title
            section = url_section or section

        # 2) title_or_json (string simples ou JSON)
        if title_or_json:
            parsed = _maybe_parse_json(title_or_json)
            if isinstance(parsed, dict):
                title = parsed.get("title") or title
                effective_lang = (parsed.get("lang") or effective_lang).strip() or "en"
                sec = parsed.get("section")
                if isinstance(sec, str):
                    section = self._clean_section_name(sec)
            else:
                title = title or title_or_json.strip()

        if not title:
            return "Please provide a valid Wikipedia page title or URL."

        # 3) Seção específica
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

        # 4) Página inteira (extract)
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

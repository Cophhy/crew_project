# src/content_creation_crew/tools/wikipedia_tool.py
from __future__ import annotations

import html
import re
from typing import Optional, List

import requests
from pydantic import BaseModel, Field, ConfigDict
from crewai.tools import BaseTool

WIKI_API = "https://{lang}.wikipedia.org/w/api.php"
UA = "CrewProject/1.0 (+https://example.org)"

# ------------------------
# Schemas (Pydantic)
# ------------------------
class WikipediaSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(..., description="Search query (plain text).")
    lang: str = Field("en", description="Wikipedia language code, e.g., 'en'.")
    limit: int = Field(5, ge=1, le=20, description="Max results (1-20).")


class WikipediaFetchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = Field(
        None, description="Exact Wikipedia page title (preferred)."
    )
    url: Optional[str] = Field(
        None,
        description="Full /wiki/ URL (may include #section). If provided, overrides 'title'.",
    )
    lang: str = Field("en", description="Wikipedia language code, e.g., 'en'.")
    section: Optional[str] = Field(
        None, description="Optional section name; if omitted, returns lead content."
    )


# ------------------------
# Tools (BaseTool)
# ------------------------
class WikipediaSearchTool(BaseTool):
    name: str = "wikipedia_search"
    description: str = (
        "Search Wikipedia using ONLY the official MediaWiki API. "
        "Returns a short, newline-separated list of 'index. Title — URL — snippet'."
    )
    args_schema = WikipediaSearchInput

    def _run(self, query: str, lang: str = "en", limit: int = 5) -> str:
        url = WIKI_API.format(lang=lang)
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
            "utf8": 1,
            "origin": "*",
        }
        r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=20)
        r.raise_for_status()
        data = r.json()

        results: List[str] = []
        for i, item in enumerate(data.get("query", {}).get("search", []), start=1):
            title = item.get("title", "")
            page_url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
            # Remove tags da snippet
            snippet = re.sub(r"<.*?>", "", item.get("snippet", "")).strip()
            results.append(f"{i}. {title} — {page_url} — {snippet}")

        if not results:
            return "No results."
        return "Wikipedia results (API)\n- " + "\n- ".join(results)

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Use sync mode.")


class WikipediaFetchTool(BaseTool):
    name: str = "wikipedia_fetch"
    description: str = (
        "Fetch plaintext from a Wikipedia page using the MediaWiki API. "
        "Pass either a 'title' or a 'url'. Optionally pass 'section' to fetch a specific section."
    )
    args_schema = WikipediaFetchInput

    def _extract_title_and_section_from_url(self, url: str) -> tuple[str, Optional[str]]:
        # Ex.: https://en.wikipedia.org/wiki/String_theory#History
        m = re.search(r"/wiki/([^#]+)(?:#(.+))?$", url)
        if not m:
            return url, None
        title = m.group(1).replace("_", " ")
        section = m.group(2).replace("_", " ") if m.group(2) else None
        return title, section

    def _fetch_section(self, lang: str, title: str, section: Optional[str]) -> str:
        api = WIKI_API.format(lang=lang)
        if section:
            # Obter índice da seção pelo nome e depois buscar essa seção
            sec_index = self._resolve_section_index(lang, title, section)
            if sec_index is None:
                return f"Section '{section}' not found in '{title}' ({lang})."
            params = {
                "action": "parse",
                "page": title,
                "prop": "wikitext",
                "section": sec_index,
                "format": "json",
            }
        else:
            params = {
                "action": "query",
                "prop": "extracts",
                "explaintext": 1,
                "titles": title,
                "format": "json",
            }

        r = requests.get(api, params=params, headers={"User-Agent": UA}, timeout=20)
        r.raise_for_status()
        data = r.json()

        # parse wikitext -> texto simples (quando section foi usado)
        if "parse" in data and "wikitext" in data["parse"]:
            wikitext = data["parse"]["wikitext"]["*"]
            # muito simples: desescapa e tira templates/refs rápidos
            text = re.sub(r"\{\{.*?\}\}", "", wikitext, flags=re.DOTALL)
            text = re.sub(r"<ref.*?</ref>", "", text, flags=re.DOTALL)
            return html.unescape(text).strip()

        # extracts (quando não há section)
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return f"Page '{title}' not found ({lang})."
        page = next(iter(pages.values()))
        extract = page.get("extract", "")
        return extract.strip() or f"No extract for '{title}' ({lang})."

    def _resolve_section_index(self, lang: str, title: str, section_name: str) -> Optional[int]:
        api = WIKI_API.format(lang=lang)
        r = requests.get(
            api,
            params={"action": "parse", "page": title, "prop": "sections", "format": "json"},
            headers={"User-Agent": UA},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        for sec in data.get("parse", {}).get("sections", []):
            if sec.get("line", "").strip().lower() == section_name.strip().lower():
                return int(sec.get("index"))
        return None

    def _run(
        self,
        title: Optional[str] = None,
        url: Optional[str] = None,
        lang: str = "en",
        section: Optional[str] = None,
    ) -> str:
        if url and not title:
            title, sec_from_url = self._extract_title_and_section_from_url(url)
            section = section or sec_from_url
        if not title:
            return "You must provide either 'title' or 'url'."

        content = self._fetch_section(lang=lang, title=title, section=section)
        head = f"=== {title} — Section: {section or 'Lead'} ==="
        return f"{head}\n{content}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Use sync mode.")

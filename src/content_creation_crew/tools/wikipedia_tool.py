# File: src/content_creation_crew/tools/wikipedia_tool.py
from __future__ import annotations
from typing import List, Optional, Tuple
import re
import requests
from crewai.tools import BaseTool  # <- usa o BaseTool do CrewAI

_WIKI_UA = "CrewAI-WikipediaTool/1.0 (https://github.com/)"

def _domain(lang: str) -> str:
    return f"https://{lang}.wikipedia.org"

def _rest_summary(lang: str, title: str) -> Optional[dict]:
    url = f"{_domain(lang)}/api/rest_v1/page/summary/{requests.utils.quote(title)}"
    r = requests.get(url, headers={"User-Agent": _WIKI_UA}, timeout=15)
    return r.json() if r.status_code == 200 else None

def _search_titles(lang: str, query: str, limit: int = 5) -> List[str]:
    url = f"{_domain(lang)}/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": str(limit),
        "format": "json",
        "utf8": 1,
    }
    r = requests.get(url, params=params, headers={"User-Agent": _WIKI_UA}, timeout=15)
    if r.status_code != 200:
        return []
    hits = r.json().get("query", {}).get("search", [])
    return [h.get("title") for h in hits if h.get("title")]

def _fetch_sections(lang: str, title: str, max_chars: int) -> Tuple[str, List[Tuple[str, str]]]:
    """Return (compact_text, external_refs[(title, url)]) using MediaWiki parse API."""
    url = f"{_domain(lang)}/w/api.php"
    params = {
        "action": "parse",
        "page": title,
        "prop": "text|externallinks",
        "format": "json",
        "utf8": 1,
    }
    r = requests.get(url, params=params, headers={"User-Agent": _WIKI_UA}, timeout=20)
    if r.status_code != 200:
        return "", []
    data = r.json()
    html = data.get("parse", {}).get("text", {}).get("*", "")
    links: List[str] = data.get("parse", {}).get("externallinks", [])

    # Extract simple paragraphs from HTML
    paras = re.findall(r"<p>(.*?)</p>", html, flags=re.IGNORECASE | re.DOTALL)

    def _clean(t: str) -> str:
        t = re.sub(r"<.*?>", "", t)
        t = re.sub(r"\[\d+\]", "", t)
        return re.sub(r"\s+", " ", t).strip()

    text_parts: List[str] = []
    total = 0
    for p in paras:
        c = _clean(p)
        if not c:
            continue
        if total + len(c) + 1 > max_chars:
            break
        text_parts.append(c)
        total += len(c) + 1
        if len(text_parts) >= 3:  # 2–3 lead paragraphs
            break

    compact = "\n\n".join(text_parts)

    # Build up to 5 external references
    refs: List[Tuple[str, str]] = []
    for u in links:
        if isinstance(u, str):
            refs.append((u.split("/")[-1][:60] or "link", u))
            if len(refs) >= 5:
                break

    return compact, refs

class WikipediaSearchTool(BaseTool):
    """Wikipedia search & summary (pt with en fallback)."""

    name: str = "wikipedia_search"
    description: str = (
        "Searches Wikipedia (pt with en fallback) and returns the first paragraphs, "
        "plus up to 5 external links. Use it to gather concise facts and references."
    )

    # Pydantic fields (become constructor kwargs automatically)
    lang: str = "pt"
    max_chars: int = 1600

    def _run(self, query: str) -> str:
        if not isinstance(query, str) or not query.strip():
            return "[wikipedia_search] Provide a non-empty text query."

        lang = (self.lang or "pt").lower()
        titles = _search_titles(lang, query, limit=5)

        used_lang = lang
        if not titles:
            used_lang = "en"
            titles = _search_titles(used_lang, query, limit=5)
            if not titles:
                return f"[wikipedia_search] No results (pt/en) for: {query}"

        title = titles[0]
        summary = _rest_summary(used_lang, title) or {}
        lead = summary.get("extract") or ""

        body, refs = _fetch_sections(used_lang, title, max_chars=max(400, self.max_chars - len(lead)))

        page_url = summary.get("content_urls", {}).get("desktop", {}).get("page") or (
            f"{_domain(used_lang)}/wiki/{requests.utils.quote(title.replace(' ', '_'))}"
        )

        parts: List[str] = [f"[Wikipedia:{used_lang}] {title} — {page_url}"]
        if lead:
            parts.append(lead.strip())
        if body:
            parts.append(body.strip())
        if refs:
            parts.append("\nExternal references (max 5):")
            parts.extend([f"{i}. {u}" for i, (_, u) in enumerate(refs, 1)])

        return "\n\n".join(parts)

# Manual test:
if __name__ == "__main__":
    tool = WikipediaSearchTool(lang="pt", max_chars=1400)
    print(tool._run("inteligência artificial na saúde"))

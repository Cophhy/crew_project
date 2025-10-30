# src/content_creation_crew/main.py
from __future__ import annotations

import json
import pathlib
import re
from typing import Any

# NOTE: match the class name you used in crew.py
# If your class is ContentCreationCrewCrew, import that:
from .crew import ContentCreationCrewCrew as ContentCreationCrew

from .schemas.article import ArticleModel


def run(topic: str = "Article topic", language: str = "en") -> ArticleModel:
    """Run the crew and return a validated ArticleModel. Also writes JSON and Markdown files."""
    result = ContentCreationCrew().crew().kickoff(
        inputs={"topic": topic, "language": language}
    )

    # 1) Prefer direct Pydantic (when task used output_pydantic=ArticleModel)
    if getattr(result, "pydantic", None):
        article: ArticleModel = result.pydantic  # type: ignore[assignment]
    else:
        # 2) Fallback: JSON dict (when output_json=True)
        data: Any | None = getattr(result, "json_dict", None)
        if data is None:
            # 3) Last resort: parse raw (strip code fences / extra text and extract JSON object)
            raw: str = getattr(result, "raw", "")
            data = _extract_first_json_object(raw)
        article = ArticleModel.model_validate(data)  # pydantic v2

    # Persist
    out_dir = pathlib.Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = article.slug or _slugify(article.title)

    json_path = out_dir / f"{slug}.json"
    md_path = out_dir / f"{slug}.md"

    json_path.write_text(
        json.dumps(article.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(article), encoding="utf-8")

    print(f"✅ Saved:\n- {json_path}\n- {md_path}")
    return article


def render_markdown(article: ArticleModel) -> str:
    lines = [f"# {article.title}", f"*{article.summary}*", ""]
    for sec in article.sections:
        lines += [f"## {sec.heading}", sec.content_md, ""]
    if article.references:
        lines.append("## References (Wikipedia)")
        for ref in article.references:
            src = f" ({ref.source})" if ref.source else ""
            lines.append(f"- [{ref.title}]({ref.url}){src}")
    return "\n".join(lines)


# ---------- helpers ----------

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", flags=re.IGNORECASE | re.MULTILINE)

def _extract_first_json_object(text: str) -> Any:
    """Extract the first top-level JSON object from arbitrary text (strips code fences if present)."""
    if not text:
        raise ValueError("Empty raw output; cannot extract JSON.")

    # Remove common code fences
    cleaned = _CODE_FENCE_RE.sub("", text).strip()

    # Fast path: try direct parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Fallback: search first {...} with balanced braces
    start = cleaned.find("{")
    if start == -1:
        raise ValueError("No JSON object found in output.")

    depth = 0
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = cleaned[start : i + 1]
                return json.loads(candidate)

    raise ValueError("Unbalanced JSON braces; cannot extract a full JSON object.")


_SLUG_SAFE_RE = re.compile(r"[^a-z0-9-]+")

def _slugify(title: str) -> str:
    s = re.sub(r"\s+", "-", title.lower().strip())
    s = _SLUG_SAFE_RE.sub("", s)
    return s.strip("-") or "article"

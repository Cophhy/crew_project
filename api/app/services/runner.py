# api/app/services/runner.py
from __future__ import annotations
import json, re
from typing import Any
from content_creation_crew.crew import ContentCreationCrewCrew
from content_creation_crew.schemas.article import ArticleDraft, ArticleModel
from .store import DB

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", flags=re.IGNORECASE | re.MULTILINE)

def create_run_id() -> str:
    import uuid
    return uuid.uuid4().hex

def _extract_first_json_object(text: str) -> Any:
    cleaned = _CODE_FENCE_RE.sub("", (text or "")).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    start = cleaned.find("{")
    if start == -1:
        raise ValueError("No JSON object found in LLM output.")
    depth = 0
    for i, ch in enumerate(cleaned[start:], start=start):
        if ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(cleaned[start:i+1])
    raise ValueError("Unbalanced braces; cannot extract JSON.")

def run_crew_sync(run_id: str, req, model_id: str, ollama_base_url: str):
    try:
        DB[run_id]["status"] = "running"
        DB[run_id]["step"] = "kickoff"

        crew = ContentCreationCrewCrew()
        inputs = {"topic": req.topic, "language": (req.language or "en").lower()}
        result = crew.crew().kickoff(inputs=inputs)

        DB[run_id]["step"] = "collect_output"

        # 1) structured → 2) raw (com cercas)
        data = getattr(result, "json_dict", None)
        if data is None:
            data = _extract_first_json_object(getattr(result, "raw", ""))

        # validação leve (ArticleDraft) → validação dura (ArticleModel >=300)
        draft = ArticleDraft.model_validate(data)
        final = ArticleModel.model_validate(draft.model_dump())

        # ✅ salve como dict (mais seguro no store em memória)
        DB[run_id]["article"] = final.model_dump()
        DB[run_id]["status"] = "finished"
        DB[run_id]["step"] = "done"

    except Exception as e:
        DB[run_id]["status"] = "failed"
        DB[run_id]["error"] = str(e)

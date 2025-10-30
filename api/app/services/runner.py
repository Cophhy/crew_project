# api/app/services/runner.py
from __future__ import annotations
import json, os, re, traceback
from typing import Any
from content_creation_crew.crew import ContentCreationCrewCrew
from content_creation_crew.schemas.article import ArticleDraft, ArticleModel
from .store import DB

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", flags=re.IGNORECASE | re.MULTILINE)

def create_run_id() -> str:
    import uuid
    return uuid.uuid4().hex

def _extract_first_json_object(text: str) -> Any:
    """Fallback: remove cercas ``` e extrai o primeiro objeto JSON balanceado."""
    cleaned = _CODE_FENCE_RE.sub("", (text or "")).strip()
    # tentativa direta
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    # varredura por chaves
    start = cleaned.find("{")
    if start == -1:
        raise ValueError("No JSON object found in LLM output.")
    depth = 0
    for i, ch in enumerate(cleaned[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(cleaned[start:i + 1])
    raise ValueError("Unbalanced braces; cannot extract JSON.")

def _pick_output(result: Any) -> Any:
    """
    Prioriza saídas estruturadas do CrewOutput/TaskOutput.
    1) pydantic -> 2) json_dict -> 3) json -> 4) raw/text
    Checa no objeto raiz e, se preciso, no último TaskOutput.
    """
    for attr in ("pydantic", "json_dict", "json", "raw", "text"):
        val = getattr(result, attr, None)
        if val:
            return val

    # fallback: olhar o último TaskOutput
    tasks = getattr(result, "tasks_output", None)
    if tasks:
        last = tasks[-1]
        for attr in ("pydantic", "json_dict", "json", "raw", "text"):
            val = getattr(last, attr, None)
            if val:
                return val

    # nada encontrado
    return None

def run_crew_sync(run_id: str, req, model_id: str, ollama_base_url: str):
    try:
        DB[run_id]["status"] = "running"
        DB[run_id]["step"] = "kickoff"

        # Garante que o ContentCreationCrewCrew use o modelo escolhido no front:
        if model_id:
            os.environ["MODEL_ID"] = model_id
        if ollama_base_url:
            os.environ["OLLAMA_BASE_URL"] = ollama_base_url

        crew = ContentCreationCrewCrew()
        inputs = {"topic": req.topic, "language": (req.language or "en").lower()}
        result = crew.crew().kickoff(inputs=inputs)

        DB[run_id]["step"] = "collect_output"

        # -------- Coleta robusta do resultado --------
        out = _pick_output(result)

        # Caso seja um objeto Pydantic do próprio pipeline (preferível)
        if isinstance(out, ArticleDraft):
            draft = out
        # Caso venha como dict já estruturado
        elif isinstance(out, dict):
            draft = ArticleDraft.model_validate(out)
        # Caso venha como string (raw/text), tenta extrair JSON
        elif isinstance(out, str):
            data = _extract_first_json_object(out)
            draft = ArticleDraft.model_validate(data)
        else:
            # último recurso: tenta json_dict no result.raw
            data = _extract_first_json_object(getattr(result, "raw", "") or "")
            draft = ArticleDraft.model_validate(data)

        # Validação final "dura" (mín. 300 palavras etc.)
        final = ArticleModel.model_validate(draft.model_dump())

        # ✅ salve como dict (mais seguro no store em memória)
        DB[run_id]["article"] = final.model_dump()
        DB[run_id]["status"] = "finished"
        DB[run_id]["step"] = "done"

    except Exception as e:
        # Registra erro detalhado pra facilitar debug
        DB[run_id]["status"] = "failed"
        DB[run_id]["error"] = f"{e}\n\n{traceback.format_exc()}"

# api/app/routers/runs.py
from __future__ import annotations
from fastapi import APIRouter, BackgroundTasks, HTTPException
from ..models import RunRequest, RunStatus, RunResult
from ..services.runner import create_run_id, run_crew_sync
from ..services.store import DB
from ..deps import SettingsDep
# ✅ para reconstruir ArticleModel na resposta
from content_creation_crew.schemas.article import ArticleModel

router = APIRouter(prefix="/runs", tags=["runs"])

@router.post("", response_model=dict, status_code=202)
def create_run(req: RunRequest, bg: BackgroundTasks, settings: SettingsDep = None):
    try:
        run_id = create_run_id()
        DB[run_id] = {"status": "queued", "step": "queued"}
        bg.add_task(run_crew_sync, run_id, req, settings.MODEL_ID, settings.OLLAMA_BASE_URL)
        return {"run_id": run_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{run_id}", response_model=RunStatus)
def get_status(run_id: str):
    data = DB.get(run_id)
    if not data:
        return RunStatus(run_id=run_id, status="failed", error="not found")
    return RunStatus(
        run_id=run_id,
        status=data["status"],
        step=data.get("step"),
        error=data.get("error"),
    )

@router.get("/{run_id}/result", response_model=RunResult)
def get_result(run_id: str):
    data = DB.get(run_id) or {}
    status = data.get("status", "failed")
    step = data.get("step")
    if status != "finished":
        # ainda não terminou ou falhou
        return RunResult(run_id=run_id, status=status, step=step, error=data.get("error"))

    # ✅ reconstrói o ArticleModel a partir do dict salvo no DB
    article_dict = data.get("article")
    article = ArticleModel.model_validate(article_dict) if article_dict else None
    return RunResult(run_id=run_id, status="finished", step="done", article=article)

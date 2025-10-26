from fastapi import APIRouter, BackgroundTasks
from ..models import RunRequest, RunStatus, RunResult
from ..services.runner import create_run_id, run_crew_sync
from ..services.store import DB
from ..deps import SettingsDep

router = APIRouter(prefix="/runs", tags=["runs"])

@router.post("", response_model=dict)
def create_run(req: RunRequest, bg: BackgroundTasks, settings: SettingsDep = None):
    run_id = create_run_id()
    DB[run_id] = {"status": "queued"}
    bg.add_task(run_crew_sync, run_id, req, settings.MODEL_ID, settings.OLLAMA_BASE_URL)
    return {"run_id": run_id}

@router.get("/{run_id}", response_model=RunStatus)
def get_status(run_id: str):
    data = DB.get(run_id)
    if not data:
        return RunStatus(run_id=run_id, status="failed", error="not found")
    return RunStatus(run_id=run_id, status=data["status"], step=data.get("step"), error=data.get("error"))

@router.get("/{run_id}/result", response_model=RunResult)
def get_result(run_id: str):
    data = DB.get(run_id)
    if not data or data.get("status") != "finished":
        return RunResult(run_id=run_id, markdown="")
    return RunResult(run_id=run_id, markdown=data["markdown"])

from fastapi import APIRouter, BackgroundTasks
from ..models import RunRequest, RunStatus, RunResult
from ..services.runner import create_run_id, run_crew_sync
from ..services.store import DB
from ..deps import SettingsDep

router = APIRouter(prefix="/runs", tags=["runs"])

#nova execução
@router.post("", response_model=dict)
def create_run(req: RunRequest, bg: BackgroundTasks, settings: SettingsDep = None):
    """
    Cria uma execucao para o processo de criação de conteúdo com base na pergunta do user (topic)
    A exec fica na fila e a task e add para processamento
    A execucao e colocada na fila e a tarefa e adicionada ao background para processamento
    Retorna o `run_id` gerado para a exec, que e usado para rastrear o status e o resultado
    """
    run_id = create_run_id()  # gera id
    DB[run_id] = {"status": "queued"}  # status em fila no banco
    
    # tarefa em exec no background
    bg.add_task(run_crew_sync, run_id, req, settings.MODEL_ID, settings.OLLAMA_BASE_URL)
    
    return {"run_id": run_id}  

#status
@router.get("/{run_id}", response_model=RunStatus)
def get_status(run_id: str):
    """
    Status da exec com base no `run_id`
    Se nao for encontrada, retorna "failed" com a mensagem "not found".
    """
    data = DB.get(run_id)  # dados da exec
    if not data:
        return RunStatus(run_id=run_id, status="failed", error="not found")  
    return RunStatus(run_id=run_id, status=data["status"], error=data.get("error"))  

#resultado
@router.get("/{run_id}/result", response_model=RunResult)
def get_result(run_id: str):
    """
    Consulta o resultado final com base no `run_id`
    Retorna o conteudo gerado se a exec for `finished`
    Se nao concluida ou nao existir, retorna vazio.
    """
    data = DB.get(run_id)
    if not data or data.get("status") != "finished":
        return RunResult(run_id=run_id, markdown="")  
    return RunResult(run_id=run_id, markdown=data["markdown"])  

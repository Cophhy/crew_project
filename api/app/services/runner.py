import uuid
from .store import DB 
from ..models import RunRequest  

# criar um ID para cada exec
def create_run_id() -> str:
    """
    O UUID gerado e convertido para uma string hexadecimal
    """
    return uuid.uuid4().hex  


# exec a crew de forma sincrona
def run_crew_sync(run_id: str, req: RunRequest, model_id: str, base_url: str):
    """
    Att o status da exec e armazena o resultado no banco
    
    """
    from content_creation_crew.crew import ContentCreationCrewCrew
    
    DB[run_id] = {"status": "running", "step": "research"}
    
    # Cria a instancia da crew 
    crew = ContentCreationCrewCrew()
    
    # Inicia o processamento da exec
    result = crew.crew().kickoff(inputs={"topic": req.topic})
    
    # atualiza o status para "finished" e armazena o conteudo
    DB[run_id] = {"status": "finished", "markdown": str(result)}  

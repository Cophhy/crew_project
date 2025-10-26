import uuid
from .store import DB
from ..models import RunRequest

def create_run_id() -> str:
    return uuid.uuid4().hex

def run_crew_sync(run_id: str, req: RunRequest, model_id: str, base_url: str):
    # importa sua crew
    from content_creation_crew.crew import ContentCreationCrewCrew
    DB[run_id] = {"status": "running", "step": "research"}
    crew = ContentCreationCrewCrew()
    # sua crew já usa o LLM e a wikipedia_tool no crew.py
    result = crew.crew().kickoff(inputs={"topic": req.topic})
    DB[run_id] = {"status": "finished", "markdown": str(result)}

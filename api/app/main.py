import os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SRC = os.path.join(ROOT, "src")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

from fastapi import FastAPI
from content_creation_crew.crew import ContentCreationCrewRunner

app = FastAPI()


class RunRequest(BaseModel):
    topic: str = Field(..., description="Tópico da pesquisa/artigo")
    # acrescente outros inputs conforme sua crew


@app.post("/run", response_model=CrewOutput)
def run_crew(req: RunRequest) -> CrewOutput:
    runner = ContentCreationCrewRunner()
    # repasse todos os campos do request como inputs
    out = runner.run(**req.model_dump())
    return out

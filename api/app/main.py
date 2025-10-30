# api/app/main.py
import os, sys
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# garante "src/" no path, inclusive no reloader
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from content_creation_crew.crew import ContentCreationCrewRunner
from content_creation_crew.schemas import CrewOutput

app = FastAPI()

# ---------- CORS ----------
# Em dev, você pode usar "*" (em prod, restrinja para o domínio do front)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # ex.: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------------

class RunRequest(BaseModel):
    topic: str = Field(..., description="Tópico do artigo")

runner = ContentCreationCrewRunner()
RUNS: Dict[str, CrewOutput] = {}

@app.post("/runs", response_model=CrewOutput)
def create_run(req: RunRequest) -> CrewOutput:
    data: Dict[str, Any] = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    out = runner.run(**data)        # execução síncrona
    RUNS[out.run_id] = out          # salva para GET/stream
    return out

@app.get("/runs/{run_id}", response_model=CrewOutput)
def get_run(run_id: str) -> CrewOutput:
    out = RUNS.get(run_id)
    if not out:
        raise HTTPException(404, "Run not found")
    return out

@app.get("/runs/{run_id}/stream")
async def stream_run(run_id: str):
    out = RUNS.get(run_id)
    if not out:
        raise HTTPException(404, "Run not found")

    # JSON string serializada por Pydantic (lida com datetime)
    json_str = out.model_dump_json() if hasattr(out, "model_dump_json") else out.json()

    async def gen():
        # Evento genérico (onmessage)
        yield f"data: {json_str}\n\n"
        # Evento nomeado (opcional)
        yield "event: run.completed\n"
        yield f"data: {json_str}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # útil atrás de proxies
            # "Connection": "keep-alive",  # opcional
        },
    )

# Compatibilidade com /run (singular)
@app.post("/run", response_model=CrewOutput)
def run_singular(req: RunRequest) -> CrewOutput:
    return create_run(req)

# Health-check simples
@app.get("/health")
def health():
    return {"status": "ok", "runs": len(RUNS)}

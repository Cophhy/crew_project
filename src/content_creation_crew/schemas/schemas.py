from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Artifact(BaseModel):
    kind: Literal["markdown", "text", "json", "file", "image"] = "markdown"
    uri: Optional[str] = None          # caminho/URL do arquivo gerado (se houver)
    content: Optional[str] = None      # conteúdo inline (quando aplicável)


class TaskResult(BaseModel):
    name: str
    status: Literal["success", "error"] = "success"
    started_at: datetime = Field(default_factory=_now_utc)
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    output_markdown: Optional[str] = None
    observations: List[str] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CrewOutput(BaseModel):
    run_id: str = Field(default_factory=lambda: uuid4().hex)
    crew: str = "content_creation_crew"
    started_at: datetime = Field(default_factory=_now_utc)
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # entradas passadas ao kickoff
    inputs: Dict[str, Any] = Field(default_factory=dict)

    # resultados intermediários (se você decidir popular)
    tasks: List[TaskResult] = Field(default_factory=list)

    # resultado final
    final_markdown: Optional[str] = None

    # arquivo final (o template padrão cria "report.md" na raiz)
    output_file: Optional[str] = None

    usage: Dict[str, Any] = Field(default_factory=dict)  # tokens, custos, etc. (opcional)


# Helpers de compatibilidade Pydantic v1/v2 (dump/json)
def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def model_to_json(model: BaseModel, **kwargs) -> str:
    if hasattr(model, "model_dump_json"):
        return model.model_dump_json(**kwargs)
    return model.json(**kwargs)

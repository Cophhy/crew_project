# src/content_creation_crew/schemas.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field  # funciona no Pydantic v1 e v2

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

class Artifact(BaseModel):
    kind: Literal["markdown", "text", "json", "file", "image"] = "markdown"
    uri: Optional[str] = None
    content: Optional[str] = None

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
    inputs: Dict[str, Any] = Field(default_factory=dict)
    tasks: List[TaskResult] = Field(default_factory=list)
    final_markdown: Optional[str] = None
    output_file: Optional[str] = None
    usage: Dict[str, Any] = Field(default_factory=dict)

# helpers opcionais
def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()

def model_to_json(model: BaseModel, **kwargs) -> str:
    return model.model_dump_json(**kwargs) if hasattr(model, "model_dump_json") else model.json(**kwargs)

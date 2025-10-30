# src/content_creation_crew/schemas.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_validator
from pydantic import conlist
from urllib.parse import urlparse

# --- Utils ---
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

# --- Artifacts ---
class Artifact(BaseModel):
    kind: Literal["markdown", "text", "json", "file", "image"] = "markdown"
    uri: Optional[str] = None
    content: Optional[str] = None

# --- Per-task outputs ---
class ResearchOutput(BaseModel):
    # v2: config por-modelo
    model_config = ConfigDict(strict=True, extra='forbid')

    bullets: conlist(str, min_length=6, max_length=10) = Field(
        ..., description="6–10 fatos verificados, baseados APENAS na Wikipedia."
    )
    sources: List[HttpUrl] = Field(
        ..., description="URLs da Wikipedia utilizadas."
    )

    @field_validator("sources")
    @classmethod
    def _only_wikipedia(cls, urls: List[HttpUrl]) -> List[HttpUrl]:
        for u in urls:
            host = (urlparse(str(u)).hostname or "").lower()
            if not host.endswith("wikipedia.org"):
                raise ValueError(f"Non-Wikipedia URL found: {u}")
        return urls


class WritingOutput(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')

    markdown: str = Field(
        ..., description="Rascunho em Markdown (apenas Wikipedia nas referências)."
    )
    references: List[HttpUrl] = Field(
        default_factory=list, description="URLs da Wikipedia citadas."
    )

    @field_validator("references")
    @classmethod
    def _only_wikipedia(cls, urls: List[HttpUrl]) -> List[HttpUrl]:
        for u in urls:
            host = (urlparse(str(u)).hostname or "").lower()
            if not host.endswith("wikipedia.org"):
                raise ValueError(f"Non-Wikipedia URL found: {u}")
        return urls


class EditOutput(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')

    markdown: str = Field(
        ..., description="Versão final em Markdown, pronta para publicação."
    )
    issues_fixed: List[str] = Field(
        default_factory=list, description="Ajustes/correções editoriais aplicadas."
    )

# --- TaskResult ---
class TaskResult(BaseModel):
    model_config = ConfigDict(strict=True, extra='ignore')

    name: str
    status: Literal["success", "error"] = "success"
    started_at: datetime = Field(default_factory=_now_utc)
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    output_markdown: Optional[str] = None
    observations: List[str] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    error_message: Optional[str] = None

    # payloads estruturados
    pydantic_model: Optional[str] = None
    pydantic_payload: Optional[Dict[str, Any]] = None
    json_dict: Optional[Dict[str, Any]] = None
    raw: Optional[str] = None

# --- CrewOutput ---
class CrewOutput(BaseModel):
    model_config = ConfigDict(strict=True, extra='ignore')

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

# --- Helpers ---
def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()

def model_to_json(model: BaseModel, **kwargs) -> str:
    return model.model_dump_json(**kwargs) if hasattr(model, "model_dump_json") else model.json(**kwargs)

__all__ = [
    "Artifact",
    "ResearchOutput",
    "WritingOutput",
    "EditOutput",
    "TaskResult",
    "CrewOutput",
    "model_to_dict",
    "model_to_json",
]

# api/app/models.py
from __future__ import annotations
from typing import Literal, Optional, Any, Dict
from pydantic import BaseModel, Field

# ✅ importe seu schema do artigo
from content_creation_crew.schemas.article import ArticleModel

class RunRequest(BaseModel):
    topic: str = Field(..., min_length=3, description="Article topic")
    language: Literal["en", "pt"] = Field("en", description="Output language")

class RunStatus(BaseModel):
    run_id: str
    status: Literal["queued", "running", "finished", "failed"]
    step: Optional[str] = None
    error: Optional[str] = None

# ✅ resultado final com o artigo tipado (Pydantic)
class RunResult(BaseModel):
    run_id: str
    status: Literal["queued", "running", "finished", "failed"]
    step: Optional[str] = None
    article: Optional[ArticleModel] = None
    error: Optional[str] = None

from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal
from datetime import datetime
import re

class ArticleSection(BaseModel):
    heading: str
    content_md: str

class Citation(BaseModel):
    title: str
    url: str
    source: Optional[str] = None
    accessed_at: Optional[datetime] = None

# Usado dentro dos TASKS (sem trava de >=300)
class ArticleDraft(BaseModel):
    title: str
    slug: str
    language: Literal["pt", "en"] = "pt"
    summary: str
    tags: List[str] = []
    author: Optional[str] = None
    sections: List[ArticleSection]
    references: List[Citation] = []
    word_count: int = Field(..., ge=1)

# Versão “dura” usada no backend/api
class ArticleModel(ArticleDraft):
    word_count: int = Field(..., ge=300, description="Minimum article body length (words)")

    @model_validator(mode="after")
    def _enforce_min_words(self):
        body = " ".join(s.content_md for s in self.sections)
        wc = len(re.findall(r"\b[\w'-]+\b", body, flags=re.UNICODE))
        if wc < 300:
            raise ValueError(f"Article body must have at least 300 words (got {wc}).")
        self.word_count = wc
        return self

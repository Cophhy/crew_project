from __future__ import annotations
from typing import Annotated
from pydantic import BaseModel, Field, conlist, constr

# Accept only canonical Wikipedia URLs (en|pt subdomains), any path/fragment allowed.
WikiUrl = Annotated[str, Field(pattern=r"^https://(en|pt)\.wikipedia\.org/.*")]

class ResearchBullet(BaseModel):
    fact: Annotated[str, Field(min_length=10, description="One concise, verifiable fact in one sentence.")]
    wikipedia_urls: Annotated[conlist(WikiUrl, min_length=1), Field(description="Canonical Wikipedia URLs only.")]

class ResearchOutput(BaseModel):
    topic: Annotated[str, Field(min_length=1)]
    language: Annotated[str, Field(pattern="^(en|pt)$")]
    bullets: conlist(ResearchBullet, min_length=6, max_length=10)

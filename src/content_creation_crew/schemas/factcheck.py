from pydantic import BaseModel, HttpUrl, Field
from typing import List, Literal, Optional

Verdict = Literal["supported", "missing_citation", "contradicted"]

class FactIssue(BaseModel):
    section_heading: str
    excerpt_or_claim: str
    verdict: Verdict
    supporting_urls: List[HttpUrl] = []
    suggested_fix: Optional[str] = None

class FactCheckReport(BaseModel):
    overall_status: Literal["pass", "needs_fixes"]
    issue_count: int = 0
    issues: List[FactIssue] = Field(default_factory=list)

from pydantic import BaseModel
from typing import Literal, Optional

class RunRequest(BaseModel):
    topic: str
    use_wikipedia: bool = True

class RunStatus(BaseModel):
    run_id: str
    status: Literal["queued", "running", "finished", "failed"]
    step: Optional[Literal["research", "writing", "editing"]] = None
    error: Optional[str] = None

class RunResult(BaseModel):
    run_id: str
    markdown: str

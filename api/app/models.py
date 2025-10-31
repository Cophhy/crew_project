from pydantic import BaseModel
from typing import Literal, Optional

# request nova exec
class RunRequest(BaseModel):
    """
    Solicitacao para nova exec do conteudo

    """
    topic: str  #assunto
    use_wikipedia: bool = True  # Wikipedia usada como fonte

#status de exec
class RunStatus(BaseModel):
    """
    Define o status

    """
    run_id: str  #id da exec
    status: Literal["queued", "running", "finished", "failed"] 
    error: Optional[str] = None  # erro se houver

#resultado
class RunResult(BaseModel):
    """
    Define o resultado final

    """
    run_id: str  # Identificador único da execução.
    markdown: str  # O conteúdo gerado pela execução, formatado em Markdown.

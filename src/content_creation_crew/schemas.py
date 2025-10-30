# src/content_creation_crew/schemas.py

from typing import List
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    conlist,
)


def _validate_wikipedia_list(urls: List[str]) -> List[str]:
    cleaned: List[str] = []
    for u in urls:
        u = u.strip()
        parsed = urlparse(u)
        scheme = (parsed.scheme or "").lower()
        host = (parsed.hostname or "").lower()

        if scheme not in {"http", "https"}:
            raise ValueError(f"URL must be http/https: {u}")
        if not host.endswith("wikipedia.org"):
            raise ValueError(f"Non-Wikipedia URL found: {u}")

        cleaned.append(u)

    # (Opcional) remover duplicados preservando ordem:
    # cleaned = list(dict.fromkeys(cleaned))
    return cleaned


class ResearchOutput(BaseModel):
    """
    Saída estruturada do research_task.
    - bullets: 6–10 fatos (strings)
    - sources: somente URLs de Wikipedia (strings; validadas no validator)
    """
    model_config = ConfigDict(strict=True, extra="forbid")

    bullets: conlist(str, min_length=6, max_length=10) = Field(
        ...,
        description="6–10 fatos verificados, baseados APENAS na Wikipedia.",
    )

    # Strings simples para garantir serialização JSON sem dor de cabeça
    sources: List[str] = Field(
        ...,
        description="URLs da Wikipedia utilizadas (apenas domínios *.wikipedia.org).",
    )

    @field_validator("sources")
    @classmethod
    def _validate_wikipedia_urls(cls, urls: List[str]) -> List[str]:
        return _validate_wikipedia_list(urls)


class CrewOutput(BaseModel):
    """
    Saída final agregada da crew.
    - research: objeto estruturado do passo de pesquisa
    - article_markdown: artigo final em Markdown (após writing/editing)
    - sources: mesmas URLs de Wikipedia usadas (serializáveis)
    """
    model_config = ConfigDict(strict=True, extra="forbid")

    research: ResearchOutput = Field(
        ..., description="Resultado estruturado do research_task."
    )

    article_markdown: str = Field(
        ...,
        description="Markdown final gerado (após writing/editing).",
    )

    sources: List[str] = Field(
        ...,
        description="Mesmas URLs de Wikipedia do research (apenas domínios *.wikipedia.org).",
    )

    @field_validator("sources")
    @classmethod
    def _validate_sources(cls, urls: List[str]) -> List[str]:
        return _validate_wikipedia_list(urls)


__all__ = ["ResearchOutput", "CrewOutput"]

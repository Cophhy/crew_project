from __future__ import annotations
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

# Detecta v2 vs v1 e prepara imports sem poluir o corpo das classes
try:
    from pydantic import HttpUrl, field_serializer
    from pydantic import ConfigDict as _ConfigDict  # alias para evitar atributo 'ConfigDict' dentro da classe
    PYDANTIC_V2 = True
except Exception:  # Pydantic v1
    from pydantic import HttpUrl
    PYDANTIC_V2 = False


class Reference(BaseModel):
    title: str = Field(..., description="Título da fonte")
    url: Optional[HttpUrl] = Field(None, description="URL da referência (se houver)")

    if PYDANTIC_V2:
        # v2: serializer para garantir que HttpUrl vire string no JSON
        @field_serializer('url')
        def _ser_url(self, v: Optional[HttpUrl], _info):
            return str(v) if v is not None else None


class Section(BaseModel):
    heading: str = Field(..., description="Título da seção")
    content: str = Field(..., description="Texto em markdown da seção")


class ResearchReport(BaseModel):
    topic: str = Field(..., description="Tema pesquisado")
    summary: str = Field(..., description="Resumo executivo (3–5 frases)")
    key_findings: List[str] = Field(..., description="Lista de achados-chave")
    sections: List[Section] = Field(default_factory=list, description="Seções do relatório")
    references: List[Reference] = Field(default_factory=list, description="Fontes citadas")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    if PYDANTIC_V2:
        # v2: permitir extras e serializar datetime como ISO 8601
        model_config = _ConfigDict(extra="allow")

        @field_serializer('generated_at')
        def _ser_dt(self, v: datetime, _info):
            return v.isoformat()
    else:
        # v1: equivalentes
        class Config:
            extra = "allow"
            json_encoders = {
                HttpUrl: str,
                datetime: lambda v: v.isoformat(),
            }

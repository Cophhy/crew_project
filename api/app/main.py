# api/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import json
import re

from .config import settings
from .routers import runs, stream  # importa os routers

# ===== Regras de contagem de palavras =====
MIN_WORDS = 300
_WORD_RE = re.compile(r"\b[\wÀ-ÿ'-]+\b", re.UNICODE)

def _count_words(text: str) -> int:
    if not isinstance(text, str):
        return 0
    return len(_WORD_RE.findall(text))

def _find_text_payload(payload):
    """
    Tenta localizar o campo de texto principal no JSON de resposta.
    Procura por chaves comuns como 'article' ou 'content'.
    Retorna (campo_encontrado:str|None, caminho:str)
    """
    if isinstance(payload, dict):
        # Campos diretos mais comuns
        for key in ("article", "content", "text", "markdown"):
            if isinstance(payload.get(key), str):
                return payload[key], key
        # Busca rasa em um nível (ex.: {"data": {"article": "..."}}
        for k, v in payload.items():
            if isinstance(v, dict):
                for key in ("article", "content", "text", "markdown"):
                    if isinstance(v.get(key), str):
                        return v[key], f"{k}.{key}"
    return None, ""

app = FastAPI(title="Crew Content API")  # <- crie o app primeiro

# CORS para o front
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Middleware de validação de mínimo de palavras =====
@app.middleware("http")
async def enforce_min_words(request: Request, call_next):
    # Ignora preflight e streaming
    if request.method == "OPTIONS" or request.url.path.startswith("/stream"):
        return await call_next(request)

    response = await call_next(request)

    # Só valida respostas JSON não-erro e não-streaming
    ctype = (response.headers.get("content-type") or "").lower()
    if response.status_code < 400 and "application/json" in ctype and getattr(response, "body", None) is not None:
        try:
            body_bytes = response.body
            payload = json.loads(body_bytes.decode("utf-8"))
            text, where = _find_text_payload(payload)
            if text:
                wc = _count_words(text)
                if wc < MIN_WORDS:
                    return JSONResponse(
                        status_code=422,
                        content={
                            "detail": f"Texto insuficiente: {wc} palavras; mínimo exigido é {MIN_WORDS}.",
                            "field": where or "article",
                            "min_words": MIN_WORDS,
                            "word_count": wc,
                        },
                    )
        except Exception:
            # Em caso de falha na leitura/parse, não bloquear a resposta.
            # (Melhor ser tolerante e deixar a rota responder)
            pass

    return response

# registre os routers depois que o app existir
app.include_router(runs.router)
app.include_router(stream.router)

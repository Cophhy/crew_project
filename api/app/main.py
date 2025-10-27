# api/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import runs, stream  # importa os routers

app = FastAPI(title="Crew Content API")  # <- crie o app primeiro

# CORS para o front
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# registre os routers depois que o app existir
app.include_router(runs.router)
app.include_router(stream.router)

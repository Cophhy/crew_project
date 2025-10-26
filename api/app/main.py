# api/app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from langdetect import detect
from src.content_creation_crew.main import run_crew  # vamos criar/ajustar já já

app = FastAPI()

class RunPayload(BaseModel):
    query: str
    model_id: str  # ex.: "llama3.1:8b-instruct", "mistral:7b-instruct", "qwen2.5:7b-instruct"

def detect_lang(text: str) -> str:
    try:
        code = detect(text)  # 'pt', 'en', ...
        return 'pt' if code.startswith('pt') else 'en'
    except Exception:
        # heurística básica de PT
        return 'pt' if any(ch in text.lower() for ch in "ãõáéíóúç") else 'en'

@app.post("/run")
def run(payload: RunPayload):
    lang = detect_lang(payload.query)
    # passa pro runner da Crew
    result = run_crew(
        user_query=payload.query,
        model_id=payload.model_id,
        lang=lang
    )
    return {"lang": lang, "model_id": payload.model_id, "result": result}

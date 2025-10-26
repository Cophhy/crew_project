from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    MODEL_ID: str = "ollama/mistral"
    ALLOW_ORIGINS: list[str] = ["http://localhost:3000"]  # Next dev

    class Config:
        env_file = ".env"

settings = Settings()

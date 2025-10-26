from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # lê .env, ignora extras desconhecidos e aceita preencher por nome/alias
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
        case_sensitive=False,  # opcional: deixa env case-insensitive
    )

    # Aceita MODEL_ID ou model (ambos funcionam)
    MODEL_ID: str = Field(
        default="ollama/mistral",
        validation_alias=AliasChoices("MODEL_ID", "model"),
    )

    # Aceita OLLAMA_BASE_URL, api_base ou OLLAMA_HOST
    OLLAMA_BASE_URL: str = Field(
        default="http://127.0.0.1:11434",
        validation_alias=AliasChoices("OLLAMA_BASE_URL", "api_base", "OLLAMA_HOST"),
    )

    # Para o front; pode deixar como lista padrão ou definir ALLOW_ORIGINS no .env como JSON
    ALLOW_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

settings = Settings()

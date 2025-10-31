from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Herda de `BaseSettings` para carregar configs do arquivo `.env` 
    e fornecer variaveis de ambiente para a aplicacao
    """
    
    # leitura do .env
    model_config = SettingsConfigDict(
        env_file=".env",  
        extra="ignore",  # ignora variaveis desconhecidas
        populate_by_name=True,  # preenche as variaveis pela correspondencia de nome
        case_sensitive=False,  # variaveis de ambiente case-insensitive
    )

    # Modelo de ID - pode ser configurado como "MODEL_ID" ou "model"
    MODEL_ID: str = Field(
        default="ollama/mistral",  # modelo usado
        validation_alias=AliasChoices("MODEL_ID", "model"),  # Permite os aliases "MODEL_ID" ou "model" no arquivo .env
    )

    # URL base para o servico do modelo
    OLLAMA_BASE_URL: str = Field(
        default="http://127.0.0.1:11434",  
        validation_alias=AliasChoices("OLLAMA_BASE_URL", "api_base", "OLLAMA_HOST"), 
    )

    ALLOW_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

#carregar as configurações
settings = Settings()

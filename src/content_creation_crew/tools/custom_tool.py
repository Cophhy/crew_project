from crewai.tools import BaseTool  
from typing import Type  
from pydantic import BaseModel, Field  

# Esquema de entrada para a ferramenta usando Pydantic
class MyCustomToolInput(BaseModel):
    """Esquema de entrada para a ferramenta personalizada MyCustomTool."""
    
    argument: str = Field(..., description="Descrição do argumento.") 

# Definindo a ferramenta personalizada que herda de BaseTool
class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    
    # Detalhando a ferramenta para que o agente entenda
    description: str = (
        "Descrição clara de para que esta ferramenta é útil. Seu agente precisará dessa informação para utilizá-la."
    )
    
    args_schema: Type[BaseModel] = MyCustomToolInput

    # Executando a logica da ferramenta
    def _run(self, argument: str) -> str:
        """Método que executa a lógica da ferramenta.
        
        Recebe um argumento de entrada e retorna uma string como saída.
        """
        return "this is an example of a tool output, ignore it and move along."

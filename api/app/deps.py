from typing import Annotated  
from fastapi import Depends  
from .config import settings  

def get_settings():
    """
    configurações carregadas da classe `Settings`.
    
    """
    return settings  

# dependencia do FastAPI que injeta as configs onde for necessario.
SettingsDep = Annotated[type(settings), Depends(get_settings)]

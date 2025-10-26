from typing import Annotated
from fastapi import Depends
from .config import settings

def get_settings():
    return settings

SettingsDep = Annotated[type(settings), Depends(get_settings)]

from fastapi import FastAPI  
from fastapi.middleware.cors import CORSMiddleware  
from .config import settings  
from .routers import runs, stream  

app = FastAPI(title="Crew Content API")  

# CORS para o front-end
app.add_middleware(
    CORSMiddleware,  
    allow_origins=settings.ALLOW_ORIGINS,  
    allow_credentials=True,  
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# routers depois que a instancia do app foi criada
app.include_router(runs.router)  
app.include_router(stream.router)  

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from api.app.services.store import DB
import asyncio, json

#router para gerenciamento
router = APIRouter(prefix="/runs", tags=["runs-stream"])

# enviar dados via SSE
async def sse_iter(run_id: str):
    """
    Funcao async que gera eventos de att sobre o status da exec via SSE
    A cada att de status "update" e enviado
    
    """
    # envia um evento inicial de "ping" para manter a conexao viva
    yield "event: ping\ndata: ok\n\n"
    last = None  # ultimo estado enviado
    while True:
        # estado atual
        data = DB.get(run_id) or {}
        
        # verifica mudanca
        if data != last:
            status_data = {"status": data.get("status"), "error": data.get("error")}
            
            # envia os dados como um evento SSE
            yield "event: update\ndata: " + json.dumps(status_data) + "\n\n"
            last = data 
            
            # status "finished"/"failed" encerra o loop
            if data.get("status") in ("finished", "failed"):
                break
        
        # 1 segundo antes de verificar novamente
        await asyncio.sleep(1)

# endpoint de streaming dos status da exec
@router.get("/{run_id}/stream")
async def stream_run(run_id: str):
    """
    Rota para enviar o status de uma exec via SSE    
    Retorna uma StreamingResponse com os dados de status da exec
    """
    return StreamingResponse(
        sse_iter(run_id),  # chama a funcao que ira gerar os eventos SSE
        media_type="text/event-stream", 
        headers={
            "Cache-Control": "no-cache",  # impede o cache da resposta
            "X-Accel-Buffering": "no",  # evita buffering em proxies
        },
    )

# api/app/routers/stream.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from api.app.services.store import DB
import asyncio, json

router = APIRouter(prefix="/runs", tags=["runs-stream"])

async def sse_iter(run_id: str):
    # envia “ping” inicial
    yield "event: ping\ndata: ok\n\n"
    last = None
    while True:
        data = DB.get(run_id) or {}
        if data != last:
            yield "event: update\ndata: " + json.dumps(data) + "\n\n"
            if data.get("status") in ("finished", "failed"):
                break
            last = data
        await asyncio.sleep(1)

@router.get("/{run_id}/stream")
async def stream_run(run_id: str):
    return StreamingResponse(sse_iter(run_id),
                             media_type="text/event-stream")

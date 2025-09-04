from __future__ import annotations
import asyncio, json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sse_starlette import EventSourceResponse

from app.workflows.graph import build_graph
from app.workflows.checkpointer import build_checkpointer


router = APIRouter(prefix="/workflows", tags=["workflows"])

# Graph compiled at startup in lifespan and stored on app.state


def _graph(request: Request):
    g = request.app.state.graph
    if not g:
        raise HTTPException(500, "Graph not initialized")
    return g


@router.get("/{name}/state")
async def get_state(
    name: str,
    thread_id: str = Query(..., description="LangGraph thread id"),
    request: Request = None,):
    graph = _graph(request)
    cfg = {"configurable": {"thread_id": thread_id}}
    snap = graph.get_state(cfg)
    return {"values": snap.values, "next": snap.next, "created_at": snap.created_at}


@router.post("/{name}/invoke")
async def invoke(
name: str,
payload: dict,
thread_id: str = Query("default"),
request: Request = None,
):
    graph = _graph(request)
    cfg = {"configurable": {"thread_id": thread_id}}
    out = graph.invoke(payload, cfg)
    return out


@router.post("/{name}/stream")
async def stream(
name: str,
payload: dict,
thread_id: str = Query("default"),
modes: list[str] = Query(["updates", "messages", "custom"]),
request: Request | None = None,
):
    graph = _graph(request)
    cfg = {"configurable": {"thread_id": thread_id}}


    async def event_gen(req: Request):
        try:
            async for item in graph.astream(payload, cfg, stream_mode=modes):
                if await req.is_disconnected():
                    break
                # item may be a tuple (mode, chunk) or a single chunk depending on stream_mode
                if isinstance(item, tuple) and len(item) == 2:
                    mode, chunk = item
                    payload_obj = {"mode": mode, "data": _serialize(chunk)}
                else:
                    payload_obj = {"mode": modes[0], "data": _serialize(item)}
                    yield {"event": "update", "data": json.dumps(payload_obj)}
        except asyncio.CancelledError:
            raise


    return EventSourceResponse(event_gen(request), headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# naive serializer for SSE JSON
def _serialize(x):
    try:
        if hasattr(x, "model_dump"):
            return x.model_dump()
        if isinstance(x, dict):
            return x
        return json.loads(json.dumps(x, default=str))
    except Exception:
        return str(x)
import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.orchestrator.router import orchestrator

router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await orchestrator.route_and_execute(request.message, request.agent_override)
        result.setdefault("agent_used", "System")
        return ChatResponse(**result)
    except Exception as e:  # noqa: BLE001
        log.exception("chat failed")
        raise HTTPException(status_code=500, detail=f"Agent execution error: {type(e).__name__}")

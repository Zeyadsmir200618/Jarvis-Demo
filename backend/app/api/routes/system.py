import os

from fastapi import APIRouter

from app.agents.registry import roster
from app.core.config import GENERATED_SITES_DIR
from app.llm.ollama_client import ollama_client
from app.models.schemas import SystemStatusResponse

router = APIRouter()


@router.get("/health")
async def health():
    """Liveness probe used by Docker health checks (no external dependencies)."""
    return {"status": "ok"}


@router.get("/status", response_model=SystemStatusResponse)
async def status():
    connected = await ollama_client.check_connection()
    return SystemStatusResponse(
        status="ok" if connected else "degraded", ollama_connected=connected, ollama_model=ollama_client.model,
        active_agents=["Root Cause Analysis (prototype)", "General Companion (experimental)", "Web Builder (experimental)"],
        generated_sites_count=len(os.listdir(GENERATED_SITES_DIR)))


@router.get("/agents")
async def agents():
    """The documented 9-agent roster + Orchestrator with honest implementation status."""
    return roster()

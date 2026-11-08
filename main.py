from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.llm.ollama_client import ollama_client
from app.models.schemas import SystemStatusResponse, ChatRequest, ChatResponse
from app.config import GENERATED_SITES_DIR
from app.agents.orchestrator import orchestrator
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("JARVIS Backend starting up...")
    # Ensure generated_sites directory exists
    GENERATED_SITES_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown
    print("JARVIS Backend shutting down...")

app = FastAPI(title="JARVIS Core API", version="0.1.0", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For demo convenience, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated websites statically
app.mount("/generated_sites", StaticFiles(directory=str(GENERATED_SITES_DIR)), name="generated_sites")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return "<h1>JARVIS Backend is Running!</h1>"

@app.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    ollama_connected = await ollama_client.check_connection()
    return SystemStatusResponse(
        status="ok" if ollama_connected else "degraded",
        ollama_connected=ollama_connected,
        ollama_model=ollama_client.model,
        active_agents=["General Companion", "Web Builder", "Root Cause Analysis"],
        generated_sites_count=len(os.listdir(GENERATED_SITES_DIR))
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_with_jarvis(request: ChatRequest):
    try:
        result = await orchestrator.route_and_execute(
            message=request.message,
            agent_override=request.agent_override
        )

        if "agent_used" not in result:
            result["agent_used"] = "System"
            
        return ChatResponse(**result)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Agent execution error: {str(e)}")

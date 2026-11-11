"""Central configuration, read from environment variables (see /.env.example)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]          # backend/
DATA_DIR = Path(os.getenv("JARVIS_DATA_DIR", BASE_DIR / "data"))
GENERATED_SITES_DIR = DATA_DIR / "generated_sites"
AUDIT_LOG_PATH = DATA_DIR / "audit.jsonl"
for _d in (DATA_DIR, GENERATED_SITES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Local LLM (Ollama runs on the host so it can use the GPU)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# MCP (host workspace server). Empty URL = MCP disabled.
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "http")               # http | stdio
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "")                  # e.g. http://host.docker.internal:8765/mcp
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")
MCP_STDIO_COMMAND = os.getenv("MCP_STDIO_COMMAND", "")            # only for running the backend on the host
JARVIS_APPROVAL_SECRET = os.getenv("JARVIS_APPROVAL_SECRET", "")

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if o.strip()]
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8000"))

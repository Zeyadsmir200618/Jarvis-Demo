import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_SITES_DIR = BASE_DIR / "generated_sites"
GENERATED_SITES_DIR.mkdir(parents=True, exist_ok=True)

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Server settings
HOST = "0.0.0.0"
PORT = 8000
# J.A.R.V.I.S. — AI-Powered Digital Twin Platform (prototype)

Graduation project, Software Engineering, Misr International University.
J.A.R.V.I.S. is designed as **nine specialized AI agents coordinated by one
Orchestrator**, reasoning over a Digital Twin of a simulated software system,
with sandbox validation, security review and **mandatory human approval** before
any change. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

> **Status: early prototype (~10% of the planned system).** Only the pieces
> marked *Implemented* below exist in code. Everything else is planned.

| Component | Status |
|---|---|
| FastAPI backend (`/health`, `/status`, `/agents`, `/chat`) | Implemented |
| Orchestrator: keyword (word-boundary) + LLM-fallback + manual routing | Partial (LangGraph planned) |
| RCA Agent: structured prompt to local Llama 3.2 over pasted text | Partial (no twin/telemetry context) |
| Next.js UI: chat, routing selector, trace panel, Workspace (MCP) panel | Implemented |
| **Host MCP server**: least-privilege access to ONE authorized project folder | Implemented, tested |
| **Approval gate + audit trail** for MCP file writes and commands | Implemented (prototype scope) |
| Docker Compose dev stack with health checks and hot reload | Implemented, tested |
| Monitoring, Detection, Prediction, Knowledge, Remediation, Validation, Security, Execution agents | Planned |
| Digital Twin, Prometheus/OpenTelemetry, PostgreSQL, LangGraph, Docker sandbox, JWT/RBAC | Planned |

The MCP workspace is a working prototype of the documented *propose → human
approval → execute → validate* path, applied to a real project folder on your PC.
It is not the full Remediation/Validation/Execution agent pipeline.

## Quick start

Prerequisites: Docker Desktop (Windows/macOS) or Docker Engine + Compose v2.24+,
Python 3.10+ on the host (for the MCP server), optionally [Ollama](https://ollama.com)
with `ollama pull llama3.2`.

```bash
python scripts/generate_secrets.py --root "C:\path\to\a\project\folder"   # creates .env + mcp-server/.env
python -m venv mcp-server/.venv
mcp-server/.venv/Scripts/pip install -r mcp-server/requirements.txt          # macOS/Linux: mcp-server/.venv/bin/pip
scripts/start-mcp-server.ps1                                                 # macOS/Linux: scripts/start-mcp-server.sh
docker compose up --build                                                    # in a second terminal
```

Open http://localhost:3000 (UI) and http://localhost:8000/docs (API).

* Docker details: [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md)
* MCP architecture, security model and setup: [docs/MCP_SETUP.md](docs/MCP_SETUP.md)
* Step-by-step live demo: [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)
* Folder structure: [docs/REPO_STRUCTURE.md](docs/REPO_STRUCTURE.md)
* What was tested / what is incomplete: [docs/STATUS.md](docs/STATUS.md)
* Changes from the original upload: [docs/MIGRATION.md](docs/MIGRATION.md)

## Tests

```bash
cd backend && pip install -r requirements-dev.txt && python -m pytest -q     # includes a live MCP round trip
cd mcp-server && pip install -r requirements.txt && python -m pytest -q
cd frontend && npm ci && npm run typecheck
```

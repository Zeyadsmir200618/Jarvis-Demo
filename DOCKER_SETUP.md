# Docker Compose setup

## Services
| Service | Image built from | Port (host) | Health check | Dev features |
|---|---|---|---|---|
| `backend` | `backend/Dockerfile` (python:3.11-slim, non-root user) | `127.0.0.1:8000` | `GET /health` every 10 s | source bind-mounted, `uvicorn --reload` |
| `frontend` | `frontend/Dockerfile` (node:20-alpine) | `127.0.0.1:3000` | `GET /` every 15 s | source bind-mounted, Next.js hot reload |

`frontend` waits for `backend` to be **healthy**. Ports bind to loopback only.
Ollama and the MCP server run on the host; containers reach them via
`host.docker.internal` (mapped with `host-gateway` so it also works on Linux).

## Commands
```bash
docker compose up --build          # build + start (foreground, Ctrl+C to stop)
docker compose up --build -d       # same, in the background
docker compose ps                  # status + health
docker compose logs -f backend     # follow one service's logs
docker compose exec backend python -m pytest -q    # run backend tests in the container
docker compose restart backend
docker compose down                # stop and remove containers (keeps the jarvis-data volume)
docker compose down -v             # also delete the audit/generated-files volume
```

## Environment variables (`.env`, created from `.env.example`)
| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Local LLM on the host |
| `OLLAMA_MODEL` | `llama3.2` | Model name pulled with `ollama pull` |
| `MCP_SERVER_URL` | `http://host.docker.internal:8765/mcp` | Host MCP endpoint; empty disables the Workspace |
| `MCP_AUTH_TOKEN` | generated | Bearer token shared with `mcp-server/.env` |
| `JARVIS_APPROVAL_SECRET` | generated | Signs one-time approval tokens; shared with `mcp-server/.env` |

`.env` is optional for compose (`required: false`): without it the stack starts with
the LLM and MCP features reporting "not connected".

## Volumes
* `./backend → /app`, `./frontend → /app`: edit on your PC, changes reload live.
* Anonymous volumes keep the container's `node_modules` and `.next` (so Windows/macOS
  host files don't clash with Linux binaries).
* Named volume `jarvis-data` keeps the audit log and generated files.

## Hot reload on Windows/macOS
File events don't cross bind mounts reliably, so polling is enabled:
`WATCHFILES_FORCE_POLLING=true` (backend) and `WATCHPACK_POLLING=true` (frontend).
After changing `requirements.txt` or `package.json`, rebuild: `docker compose up --build`.

## Requirements
Docker Desktop 4.27+ (Compose v2.24+, for `env_file: required: false`) or Docker Engine
with the compose plugin. On Windows use the WSL 2 backend; keep the repo on a local
drive.

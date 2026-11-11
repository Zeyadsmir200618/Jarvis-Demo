# Repository structure

```
jarvis/
├── README.md                     overview, status table, quick start
├── docker-compose.yml            dev stack: backend + frontend (health checks, hot reload)
├── .env.example                  backend/compose settings (copy to .env — git-ignored)
├── docs/                         architecture, MCP, Docker, demo, status, migration notes
├── scripts/
│   ├── generate_secrets.py       creates .env + mcp-server/.env with matching random secrets
│   └── start-mcp-server.ps1|.sh  starts the host MCP server
├── backend/                      FastAPI service (runs in Docker)
│   ├── Dockerfile, .dockerignore, requirements*.txt
│   ├── app/
│   │   ├── main.py               app factory, CORS, routers
│   │   ├── core/                 config (env vars), logging with secret redaction
│   │   ├── api/routes/           system (/health,/status,/agents), chat, workspace (MCP + approvals)
│   │   ├── orchestrator/         prototype router (keyword + LLM fallback + manual + workspace route)
│   │   ├── agents/
│   │   │   ├── registry.py       the documented 9 agents + Orchestrator with honest status
│   │   │   ├── base.py           common agent contract (typed step logs)
│   │   │   ├── rca/              Root Cause Analysis Agent (prompt-based prototype)
│   │   │   └── experimental/     general chat + web builder (framework experiments, out of scope)
│   │   ├── integrations/mcp/     MCP client (Streamable HTTP or stdio)
│   │   ├── approvals/            pending-action queue, one-time token minting, audit trail
│   │   ├── workspace/            inspect / propose edit / commands via MCP (approval-gated)
│   │   ├── llm/                  Ollama client
│   │   └── models/               Pydantic schemas
│   └── tests/                    router, roster, and a live end-to-end MCP workflow test
├── frontend/                     Next.js 14 + TypeScript + Tailwind (runs in Docker)
│   ├── Dockerfile, .dockerignore, package.json, package-lock.json
│   └── src/app (page, layout, styles), src/components/WorkspacePanel.tsx
├── mcp-server/                   HOST-side MCP server (not in Docker)
│   ├── jarvis_mcp_server/        server (tools/resources), policy, approval verifier, command allow-list
│   ├── tests/                    policy tests + real MCP round trip over HTTP
│   ├── .env.example, requirements.txt, claude_desktop_config.example.json
└── sample-data/
    ├── demo-project/             tiny service with one intentional failing test (MCP demo target)
    └── incidents/                synthetic incident texts for the RCA prototype
```

## Planned modules (deliberately not created yet)
Empty folders would suggest work that doesn't exist. Each planned module gets its
folder when its first real code lands, at these locations:

| Planned module | Target location | Roadmap |
|---|---|---|
| Simulated ecosystem (5 services + PostgreSQL) | `environment/` + its own compose file | M2 |
| Telemetry (Prometheus, OpenTelemetry, ingestion) | `backend/app/telemetry/`, `infra/monitoring/` | M3 |
| Digital Twin API + data model | `backend/app/digital_twin/` | M4 |
| LangGraph Orchestrator + Incident Context | `backend/app/orchestrator/graph.py` | M5 |
| Monitoring, Detection agents | `backend/app/agents/monitoring/`, `agents/detection/` | M3–M5 |
| Prediction, Knowledge, Remediation agents | `backend/app/agents/{prediction,knowledge,remediation}/` | M6 |
| Validation (Docker sandbox), Security, Execution agents | `backend/app/agents/{validation,security,execution}/`, `infra/sandbox/` | M7 |
| JWT/RBAC, approval dashboard | `backend/app/auth/`, `frontend/src/app/approvals/` | M7 |
| CI (GitHub Actions) | `.github/workflows/` | M6–M8 |

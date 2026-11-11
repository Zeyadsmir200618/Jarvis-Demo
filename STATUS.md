# What was tested, and what remains incomplete (11 Nov 2026)

## Tested
| Test | Result | How |
|---|---|---|
| MCP server policy (path escape, symlink escape, protected files, root refusal) | Pass | `mcp-server/tests` (pytest) |
| Approval tokens (wrong target, replay, expiry, wrong secret) | Pass | `mcp-server/tests` |
| Real MCP round trip over Streamable HTTP: list tools/resources, read, refused `.env`, gated write, tests fail → fix → pass | Pass | `mcp-server/tests::test_mcp_end_to_end` (real server subprocess, official SDK client) |
| Bearer auth rejects wrong token | Pass | `mcp-server/tests` |
| Backend: health, 9-agent roster, router incl. the old "login" misroute | Pass | `backend/tests` |
| Backend ↔ MCP end-to-end through the REST API (inspect, pending/approve/reject, write, tests, path escape → 400, audit) | Pass | `backend/tests::test_full_mcp_workflow` |
| Frontend TypeScript typecheck | Pass | `npx tsc --noEmit` |
| `docker compose up --build`: both services build, start and report **healthy**; frontend waits for backend health | Pass* | Docker Engine 29.9, Compose v5.7 (Linux) |
| Containerized backend → **host** MCP server via `host.docker.internal` (host-gateway) | Pass* | MCP bound to the docker bridge gateway |
| Full UI workflow in a browser (Playwright): connect → inspect → run_tests (fail) → propose diff → approve → run_tests (pass) → compose_up → compose_ps → compose_down → audit | Pass* | demo service answered `{"message": "Hello, Ada!"}` on :8081 |
| Hot reload: backend file edit picked up by uvicorn; frontend edit picked up by Next.js | Pass* | bind mounts + polling |
| Secrets absent from backend and MCP logs | Pass* | grep of logs for both secret values |
| Backend tests inside the container | Pass (6 passed, 1 skipped — the MCP integration test needs the host-side package) | `docker compose exec backend pytest` |

\*Test environment caveat: the sandbox could not download images from Docker Hub, so
`python:3.11-slim` and `node:20-alpine` were **locally built stand-ins with the same
tags** (Ubuntu-based, Python 3.11, Node 22). The project's Dockerfiles and compose file
were used unchanged, but the real official base images were not exercised. Run
`docker compose up --build` once on your PC to confirm.

## Not tested here
* Windows / Docker Desktop specifics (paths, `host.docker.internal` to loopback, PowerShell script). Documented, not run.
* LLM-generated edits and LLM summaries: Ollama models could not be downloaded in the sandbox, so the LLM path ran in its offline fallback. The find/replace path (same approval flow) was tested.
* Claude Desktop stdio configuration example.

## Incomplete (by design, planned in the roadmap)
* 8 of the 9 agents (Monitoring, Detection, Prediction, Knowledge, Remediation, Validation, Security, Execution); RCA is a prompt-only prototype over pasted text.
* LangGraph Orchestrator and Incident Context; Digital Twin; Prometheus/OpenTelemetry; PostgreSQL/Elasticsearch; Docker sandbox; Semgrep; JWT/RBAC; CI.
* The approval queue is in memory (pending actions are lost on backend restart; the audit log persists). The backend API has no authentication — acceptable on loopback for a demo, not beyond.
* Chat replies still show raw Markdown; execution-trace steps are descriptive labels.

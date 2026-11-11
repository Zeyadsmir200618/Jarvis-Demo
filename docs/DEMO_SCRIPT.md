# Live demo script (≈ 6 minutes)

## Before the discussion (once, then rehearse twice)
- [ ] Copy `sample-data/demo-project` to e.g. `C:\jarvis-demo\demo-project` (the original keeps its failing test for the next run).
- [ ] `python scripts/generate_secrets.py --root C:\jarvis-demo\demo-project`
- [ ] Ollama running with `llama3.2` pulled; warm it with one prompt.
- [ ] Terminal 1: `scripts\start-mcp-server.ps1` (shows "Authorized project root: …").
- [ ] Terminal 2: `docker compose up --build`; wait until `docker compose ps` shows both services **healthy**.
- [ ] Docker Desktop running (the demo project is started on the host by `compose_up`).
- [ ] Browser tabs: http://localhost:3000 and the demo project folder in Explorer/VS Code.
- [ ] Backup: a screen recording of a full successful run.

## Part A — Prototype RCA (≈ 2 min)
1. Header shows Ollama status. Paste in **Auto** mode:
   `Incident: PaymentService crashed with psycopg2.OperationalError: connection pool exhausted after deployment v2.3`
   → label shows **Root Cause Analysis Agent**. Say: "keyword router → prompt-based RCA on a local Llama 3.2."
2. Open **Show Execution Logs**. Say: "these step labels are descriptive; real traces come with LangGraph."

## Part B — MCP workspace (≈ 4 min)
| # | Do | Say |
|---|---|---|
| 1 | Click **Workspace (MCP)** | "The backend is an MCP client. It just connected to a real MCP server on this PC — 8 tools, one authorized folder." |
| 2 | Chat: `Please inspect the project on my PC` (or **Inspect project**) | "Read-only tools: tree and key files. `.env` and `.git` are invisible by policy." |
| 3 | Click `run_tests 🔒` → approval appears → **Approve** | "Running code needs my approval. Result: 1 failed — greeting lacks '!'." |
| 4 | Instruction: `make greeting() end with an exclamation mark` → **Propose change** (fallback: find/replace) | "The LLM proposes; the MCP server computes the diff. Nothing is written yet." |
| 5 | Show the diff in the amber **Human approval gate**; point at the unchanged file in VS Code | "This is the gate. The server refuses writes without a one-time token that only my click creates." |
| 6 | **Approve** → file changes on disk | "The token is bound to this exact content and expires in 2 minutes." |
| 7 | `run_tests 🔒` → Approve → **1 passed** | "Validation after the change." |
| 8 | `compose_up 🔒` → Approve; then `compose_ps`; open http://127.0.0.1:8081/greet/Ada | "Starting services changes the environment, so it's gated. ps/logs are read-only." |
| 9 | `compose_down 🔒` → Approve; scroll to **Audit trail** | "Every proposal and decision is logged." |

Close: "This is a working slice of our documented propose → approve → execute →
validate path on a real folder. The nine agents, Digital Twin and telemetry are the
roadmap."

## Don'ts
* Don't say the 9 agents are implemented; only the RCA prototype exists.
* Don't authorize your home folder; authorize only the demo project.
* Don't show `.env` contents on screen.
* If the LLM is slow or off, use the find/replace fallback — it exercises the same approval path.

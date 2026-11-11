# Architecture: the Orchestrator and the nine agents

Source of truth: *Technical System Design & Architecture* (Sections 18–19, Table 3,
Section 49) and the *final Project Management Plan*. The earlier proposal and the
MIU review paper describe an older 7-agent roster; the mapping below shows how each
older name carries into the 9-agent design. No agent was removed or invented.

## Roster

The **Orchestrator / Planner** is *not* one of the nine agents: it owns the Incident
Context, decides which agent runs next (LangGraph conditional edges), applies the
bounded-retry rules and writes every transition to the audit trail. The **human
approval step is a governance gate, not an agent** (Design doc §18.1, §33).

| # | Agent | Input → Output | Hands off to | Phase | Status |
|---|---|---|---|---|---|
| 1 | Monitoring | twin telemetry → anomalies, alerts | Orchestrator | Core MVP (M3–M5) | Planned |
| 2 | Incident Detection | alerts → de-duplicated Incident record + severity | Orchestrator, RCA | Core MVP (M3–M5) | Planned |
| 3 | Root Cause Analysis | incident + metrics/logs/traces/dependencies/deployments → ranked causes, evidence, 0–1 confidence | Orchestrator; Prediction, Remediation | Core MVP (M5) | **Partial** (prompt-only prototype) |
| 4 | Remediation | root cause + context → ranked candidates, least-invasive first | Validation | Core MVP (M6) | Planned |
| 5 | Validation | candidate → pre-checks + Docker-sandbox pass/fail | Security (pass) / Remediation (fail) | Core MVP (M7) | Planned |
| 6 | Security | candidate change → baseline security review, risk level; **Semgrep optional** | Orchestrator → human | Core MVP (M7) | Planned |
| 7 | Execution | human-approved action → result + post-action state | Orchestrator → Knowledge | Core MVP (M7) | Planned |
| 8 | Knowledge | closed incidents ↔ similar past incidents | RCA, Remediation | Storage in MVP (M6); similarity search extension | Planned |
| 9 | Prediction | history → failure probability, lead time (selected patterns) | Orchestrator | Advanced extension (M6+) | Planned |

### Why this MVP split
* **Seven agents are needed for one complete incident loop** (detect → diagnose →
  propose → validate → review → execute). The PM plan's M7 acceptance test is a
  full trial "fault injection to human-approved, executed action", which needs
  Monitoring, Detection, RCA, Remediation, Validation, Security and Execution.
* **Security** stays core as a baseline review (MIU paper, team decision); Semgrep
  is the optional deeper scanner (Design doc Table 17).
* **Knowledge**: append-only incident storage is core (proposal FR-12); similarity
  retrieval is an extension (Design doc §49, MIU paper PRQ5).
* **Prediction** is an advanced extension (proposal Table 12, Design doc Table 17),
  but remains part of the architecture.

### Name reconciliation
| Older documents (proposal / MIU paper) | 9-agent design |
|---|---|
| Monitoring & Observability Agent | Monitoring Agent |
| — (folded into Monitoring) | **Incident Detection Agent** (new, separate) |
| Predictive Failure Detection Agent | Prediction Agent |
| Remediation Generation Agent | Remediation (Recommendation) Agent |
| Testing & Validation Agent | Validation Agent |
| Security Analysis Agent | Security Agent |
| "controlled execution step" | **Execution Agent** (formalized, Design doc §18.1) |
| "Incident Knowledge Base" (storage) | **Knowledge Agent** |
| Code Analysis Agent (advanced) | Not a separate agent in the 9-agent design; source-code/deployment context is an input to RCA and Remediation (advanced extension) |

## Where MCP fits
MCP is an **integration layer, not a tenth agent**. The backend is an MCP client;
the host MCP server exposes a least-privilege workspace. In the full system the
Execution Agent and Validation Agent would use such tools; today the Workspace panel
exercises the same propose → approve → execute → validate path on a real folder.
See [MCP_SETUP.md](MCP_SETUP.md).

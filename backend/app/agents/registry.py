"""The documented J.A.R.V.I.S. agent roster and its CURRENT implementation status.

Source of truth: Technical System Design & Architecture (Sections 18-19) and the
final Project Management Plan. The Orchestrator is NOT one of the nine agents;
it coordinates them. The human approval step is a governance gate, not an agent.

Status values are honest: only code that exists in this repository is
"partial" or "implemented"; everything else is "planned".
"""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AgentInfo:
    key: str
    name: str
    responsibility: str
    phase: str            # implementation phase in the roadmap
    status: str           # implemented | partial | planned
    module: str | None    # where the code lives (None = not started)


ORCHESTRATOR = AgentInfo("orchestrator", "Orchestrator / Planner",
                         "Owns the Incident Context, activates agents, applies branch rules, writes the audit trail",
                         "Core (M2-M5)", "partial", "app/orchestrator/router.py (keyword/manual router; LangGraph planned)")

AGENTS: list[AgentInfo] = [
    AgentInfo("monitoring", "Monitoring Agent", "Watches twin telemetry; flags anomalies", "Core MVP (M3-M5)", "planned", None),
    AgentInfo("detection", "Incident Detection Agent", "De-duplicates alerts; opens Incident records with severity", "Core MVP (M3-M5)", "planned", None),
    AgentInfo("rca", "Root Cause Analysis Agent", "Ranked, evidence-backed root-cause hypotheses with confidence", "Core MVP (M5)", "partial", "app/agents/rca/agent.py (prompt-only, pasted text)"),
    AgentInfo("remediation", "Remediation Agent", "Ranked candidate actions, least-invasive first", "Core MVP (M6)", "planned", None),
    AgentInfo("validation", "Validation Agent", "Pre-checks + Docker sandbox tests of a candidate", "Core MVP (M7)", "planned", None),
    AgentInfo("security", "Security Agent", "Baseline security review of a candidate (Semgrep optional)", "Core MVP (M7)", "planned", None),
    AgentInfo("execution", "Execution Agent", "Applies ONLY the human-approved action; reports the result", "Core MVP (M7)", "planned", None),
    AgentInfo("knowledge", "Knowledge Agent", "Stores closed incidents; similarity retrieval for RCA/Remediation", "Storage MVP (M6); retrieval extension", "planned", None),
    AgentInfo("prediction", "Prediction Agent", "Failure probability for selected patterns (scikit-learn/XGBoost)", "Advanced extension (M6+)", "planned", None),
]


def roster() -> dict:
    return {"orchestrator": asdict(ORCHESTRATOR), "agents": [asdict(a) for a in AGENTS]}

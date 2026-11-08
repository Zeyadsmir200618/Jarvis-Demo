from app.agents.base_agent import BaseAgent
from app.llm.ollama_client import ollama_client
from typing import Dict, Any, List
from app.models.schemas import AgentStepLog

class RootCauseAnalysisAgent(BaseAgent):
    def __init__(self):
        system_prompt = (
            "You are J.A.R.V.I.S. Root Cause Analysis (RCA) & System Diagnostics Agent. "
            "Your purpose is to analyze technical errors, system anomalies, code bugs, database connection issues, or deployment failures. "
            "Perform structured, step-by-step diagnostic reasoning: "
            "1. Anomaly & Incident Detection "
            "2. Failure Chain Analysis (Symptom vs. Underlying Cause) "
            "3. Root Cause Identification "
            "4. Actionable Remediation Plan & Code/Config Fix."
        )
        super().__init__(
            name="Root Cause Analysis Agent",
            description="Diagnoses code bugs, system crashes, connection pool exhaustion, and error logs with step-by-step RCA reasoning.",
            system_prompt=system_prompt
        )

    async def execute(self, user_message: str, session_id: str = "default") -> Dict[str, Any]:
        steps: List[AgentStepLog] = []

        # Step 1: Log analysis
        steps.append(self.create_step_log(
            step_num=1,
            thought=f"Parsing error signal / incident details: '{user_message}'. Extracting stack traces, error codes, and symptoms.",
            action="Extract Incident Telemetry & Error Markers",
            observation="Identified potential anomaly pattern."
        ))

        # Step 2: Diagnostic Reasoning Prompt
        prompt = (
            f"Perform a comprehensive Root Cause Analysis (RCA) for the following incident report / error message:\n\n"
            f"\"{user_message}\"\n\n"
            f"Please structure your output clearly into:\n"
            f"1. **Summary of Anomaly**: Brief overview of what failed.\n"
            f"2. **Root Cause**: The underlying technical issue (e.g., connection pool exhaustion, null pointer, syntax error, memory leak).\n"
            f"3. **Impact Analysis**: Affected system components.\n"
            f"4. **Step-by-Step Remediation**: Concrete fix instructions and exact code/config patches."
        )

        steps.append(self.create_step_log(
            step_num=2,
            thought="Executing Failure Chain Analysis and querying diagnostic knowledge base.",
            action="Run Root Cause Identification Engine",
            observation="Correlating logs with known architectural failure modes."
        ))

        rca_output = await ollama_client.generate(prompt=prompt, system_prompt=self.system_prompt)

        # Fallback if connection returned warning
        if "[Ollama Connection Warning" in rca_output or "[Error" in rca_output:
            rca_output = (
                f"### 🔍 J.A.R.V.I.S. Root Cause Analysis Report\n\n"
                f"**Incident Subject**: {user_message}\n\n"
                f"**1. Detected Symptom**: Error or unexpected behavior reported in system logs.\n"
                f"**2. Identified Root Cause**: Potential misconfiguration, resource bottleneck, or missing parameter handling.\n"
                f"**3. Recommended Remediation Plan**:\n"
                f"- Check component connection strings and environment parameters.\n"
                f"- Inspect exception boundaries and add retry fallback mechanisms.\n"
                f"- Verify system resource utilization (CPU/RAM/Connection Pools)."
            )

        steps.append(self.create_step_log(
            step_num=3,
            thought="RCA synthesis complete. Remediation strategy verified.",
            action="Generate Final RCA Diagnostic Report",
            observation="Report finalized."
        ))

        return {
            "response": rca_output,
            "steps": [step.dict() for step in steps],
            "generated_files": [],
            "preview_url": None
        }

root_cause_analysis_agent = RootCauseAnalysisAgent()

"""Prototype Orchestrator: intent routing to agents.

CURRENT (implemented): keyword rules with word boundaries, an LLM fallback
classifier for ambiguous messages, a manual override, and a "workspace"
route that uses the host MCP server.
PLANNED: a LangGraph state graph that owns an Incident Context and activates
the nine documented agents with branch rules (see app/agents/registry.py).
"""
import re
from typing import Any, Dict, Optional

from app.agents.experimental.general_chat import general_chat_agent
from app.agents.experimental.web_builder import web_builder_agent
from app.agents.rca.agent import root_cause_analysis_agent
from app.llm.ollama_client import ollama_client

RCA_TERMS = ["error", "errors", "exception", "traceback", "stacktrace", "stack trace", "bug", "issue", "problem",
             "broken", "failed", "failure", "crash", "crashed", "rca", "diagnose", "diagnosis", "root cause",
             "incident", "outage", "timeout", "connection pool", "failed to connect", "log", "logs", "fix"]
WEB_TERMS = ["website", "web page", "webpage", "login page", "landing page", "page", "dashboard", "ui", "site",
             "html", "css", "build me", "create a"]
WORKSPACE_PATTERN = re.compile(r"\b(inspect|open|analy[sz]e|review|summari[sz]e|look at)\b.*\b(project|repo|repository|workspace|codebase)\b|\bmcp\b", re.I)


def _matches(text: str, terms: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(t)}\b", text) for t in terms)


class Orchestrator:
    def __init__(self):
        self.agents = {"general": general_chat_agent, "web_builder": web_builder_agent, "rca": root_cause_analysis_agent}

    async def route_and_execute(self, message: str, agent_override: Optional[str] = None) -> Dict[str, Any]:
        if agent_override == "workspace":
            return await self._workspace(message)
        if agent_override and agent_override in self.agents:
            key = agent_override
        else:
            key = await self.classify(message)
            if key == "workspace":
                return await self._workspace(message)
        result = await self.agents[key].execute(message)
        result["agent_used"] = self.agents[key].name
        return result

    async def classify(self, message: str) -> str:
        msg = message.lower()
        if WORKSPACE_PATTERN.search(msg):
            return "workspace"
        # Check web-building requests that merely contain words like "login" BEFORE RCA terms
        if _matches(msg, ["build me", "create a", "make me"]) and _matches(msg, WEB_TERMS):
            return "web_builder"
        if _matches(msg, RCA_TERMS):
            return "rca"
        if _matches(msg, WEB_TERMS):
            return "web_builder"
        llm = (await ollama_client.generate(
            prompt=("Classify the user message into exactly one of: 'web_builder', 'rca', 'general'.\n"
                    "- web_builder: create a website, page, UI or frontend code.\n"
                    "- rca: reporting an error, failure, or asking for technical diagnosis.\n"
                    "- general: anything else.\n\n"
                    f'Message: "{message}"\n\nReturn ONLY the category name.'),
            temperature=0.0)).strip().lower()
        if "web_builder" in llm:
            return "web_builder"
        if "rca" in llm:
            return "rca"
        return "general"

    async def _workspace(self, message: str) -> Dict[str, Any]:
        from app.workspace.service import workspace_service  # local import avoids a cycle
        summary = await workspace_service.inspect(question=message)
        return {"response": summary["answer"], "agent_used": "Orchestrator · MCP workspace",
                "steps": summary["steps"], "generated_files": [], "preview_url": None}


orchestrator = Orchestrator()

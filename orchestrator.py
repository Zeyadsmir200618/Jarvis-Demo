from typing import Dict, Any, List
from app.agents.general_chat_agent import general_chat_agent
from app.agents.web_builder_agent import web_builder_agent
from app.agents.root_cause_analysis_agent import root_cause_analysis_agent
from app.llm.ollama_client import ollama_client

class Orchestrator:
    def __init__(self):
        self.agents = {
            "general": general_chat_agent,
            "web_builder": web_builder_agent,
            "rca": root_cause_analysis_agent
        }

    async def route_and_execute(self, message: str, agent_override: str = None) -> Dict[str, Any]:
        """Classifies the user message and routes it to the most relevant agent."""

        # 1. Check for manual override
        if agent_override and agent_override in self.agents:
            return await self.agents[agent_override].execute(message)

        # 2. Intelligent Routing Logic (Intent Classification)
        # We'll use a simple keyword-based classifier + LLM classification for robustness
        intent = await self._classify_intent(message)

        selected_agent_key = intent if intent in self.agents else "general"

        print(f"Orchestrator routed message to: {selected_agent_key}")

        result = await self.agents[selected_agent_key].execute(message)
        result["agent_used"] = self.agents[selected_agent_key].name

        return result

    async def _classify_intent(self, message: str) -> str:
        """Determines the intent of the user message."""
        msg_lower = message.lower()

        # Immediate keyword matching for high-priority intents
        web_keywords = ["website", "login page", "page", "dashboard", "ui", "site", "landing page", "code", "build me", "create a", "css", "html"]
        rca_keywords = ["error", "fix", "bug", "issue", "problem", "broken", "failed", "crash", "rca", "diagnosis", "analysis", "why did", "connection pool", "failed to connect", "stacktrace", "log", "incident"]

        # Check for RCA first (Safety & Technical Diagnosis)
        if any(kw in msg_lower for kw in rca_keywords):
            return "rca"

        # Check for Web Building
        if any(kw in msg_lower for kw in web_keywords):
            return "web_builder"

        # LLM based classification for ambiguous cases
        classification_prompt = (
            "Classify the following user message into exactly one of these categories: 'web_builder', 'rca', 'general'.\n"
            "- 'web_builder': If they want to create a website, page, UI, dashboard, or write frontend code.\n"
            "- 'rca': If they are reporting an error, bug, failure, or asking for technical diagnosis.\n"
            "- 'general': For everything else: conversation, questions, advice, philosophy, general knowledge.\n\n"
            f"Message: \"{message}\"\n\n"
            "Return ONLY the category name."
        )

        llm_intent = await ollama_client.generate(prompt=classification_prompt, temperature=0.0)

        # Clean up LLM response
        llm_intent = llm_intent.strip().lower()
        if "web_builder" in llm_intent: return "web_builder"
        if "rca" in llm_intent: return "rca"

        return "general"

orchestrator = Orchestrator()

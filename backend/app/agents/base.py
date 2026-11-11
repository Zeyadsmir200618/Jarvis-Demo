from typing import List, Dict, Any, Optional
from app.models.schemas import AgentStepLog
from app.llm.ollama_client import ollama_client

class BaseAgent:
    def __init__(self, name: str, description: str, system_prompt: str):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt

    async def execute(self, user_message: str, session_id: str = "default") -> Dict[str, Any]:
        """Base execution template to be implemented by sub-agents.
        Returns a dictionary with 'response', 'steps', 'generated_files', and 'preview_url'.
        """
        raise NotImplementedError("Subclasses must implement execute()")

    def create_step_log(self, step_num: int, thought: str, action: Optional[str] = None, observation: Optional[str] = None) -> AgentStepLog:
        return AgentStepLog(
            step=step_num,
            thought=thought,
            action=action,
            observation=observation
        )

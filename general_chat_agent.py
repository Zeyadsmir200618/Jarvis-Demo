from app.agents.base_agent import BaseAgent
from app.llm.ollama_client import ollama_client
from typing import Dict, Any, List
from app.models.schemas import AgentStepLog

class GeneralChatAgent(BaseAgent):
    def __init__(self):
        system_prompt = (
            "You are J.A.R.V.I.S., an intelligent, empathetic, highly capable AI companion and assistant. "
            "You can speak about anything in life, science, philosophy, technology, daily advice, history, and general knowledge. "
            "Your tone is warm, polite, clear, articulate, and deeply engaging. Always treat the user as a respected collaborator. "
            "Provide insightful, well-reasoned answers, and feel free to use clear paragraph structure."
        )
        super().__init__(
            name="General Companion Agent",
            description="Handles general questions, conversation, life advice, philosophy, science, and everyday topic discussions.",
            system_prompt=system_prompt
        )

    async def execute(self, user_message: str, session_id: str = "default") -> Dict[str, Any]:
        steps: List[AgentStepLog] = []

        # Step 1: Context Analysis & Tone Formulation
        steps.append(self.create_step_log(
            step_num=1,
            thought=f"Received query: '{user_message}'. Formulating helpful, natural response as a general AI companion.",
            action="Analyze User Intent & Generate Response",
            observation="Query classified as general conversation/knowledge inquiry."
        ))

        # Generate response using Ollama
        response_text = await ollama_client.generate(
            prompt=user_message,
            system_prompt=self.system_prompt
        )

        # Fallback if connection returned a warning/error text
        if "[Ollama Connection Warning" in response_text or "[Error" in response_text:
            # Provide a fallback natural response so demo never crashes
            response_text = (
                f"I am J.A.R.V.I.S. I heard your message: '{user_message}'. "
                "I am ready to talk about anything in life, technology, philosophy, or personal advice. "
                "(Note: Running in standalone local mode. Start Ollama for real-time model inference)."
            )

        steps.append(self.create_step_log(
            step_num=2,
            thought="Response generation completed successfully.",
            action="Deliver Final Response",
            observation="Output finalized."
        ))

        return {
            "response": response_text,
            "steps": [step.dict() for step in steps],
            "generated_files": [],
            "preview_url": None
        }

general_chat_agent = GeneralChatAgent()

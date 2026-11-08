from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str = Field(..., description="User prompt or question")
    agent_override: Optional[str] = Field(None, description="Force specific agent: 'general', 'web_builder', or 'auto'")
    session_id: Optional[str] = Field("default_session", description="Session identifier for conversation memory")

class AgentStepLog(BaseModel):
    step: int
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None

class ChatResponse(BaseModel):
    response: str = Field(..., description="Final assistant response")
    agent_used: str = Field(..., description="Name of the agent that handled the request")
    steps: List[AgentStepLog] = Field(default=[], description="Execution trace and reasoning steps")
    preview_url: Optional[str] = Field(None, description="URL to preview generated website if applicable")
    generated_files: List[str] = Field(default=[], description="List of created files")

class SystemStatusResponse(BaseModel):
    status: str
    ollama_connected: bool
    ollama_model: str
    active_agents: List[str]
    generated_sites_count: int

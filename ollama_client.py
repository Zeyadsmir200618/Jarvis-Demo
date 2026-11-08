import httpx
import json
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL

class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model

    async def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                else:
                    return f"[Error: Ollama status {response.status_code}]"
        except Exception as e:
            # Print full exception details for debugging
            return f"[Ollama Connection Warning: Could not connect to {self.base_url}. Details: {type(e).__name__} - {str(e)}]"

    async def check_connection(self) -> bool:
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False

ollama_client = OllamaClient()
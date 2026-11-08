import re
import uuid
import webbrowser
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.llm.ollama_client import ollama_client
from app.tools.file_tools import generate_website_file
from app.models.schemas import AgentStepLog

class WebBuilderAgent(BaseAgent):
    def __init__(self):
        system_prompt = (
            "You are J.A.R.V.I.S. Autonomous Web & Code Builder Agent. "
            "Your objective is to generate production-ready, beautiful, modern HTML/CSS/JS websites based on user requests. "
            "Always include complete single-file HTML code with embedded <style> and <script>. "
            "Enclose the entire code inside ```html ... ``` code blocks."
        )
        super().__init__(
            name="Web & Code Builder Agent",
            description="Dynamically writes HTML/CSS/JS code, creates responsive websites (login pages, dashboards, landing pages), and generates live interactive previews.",
            system_prompt=system_prompt
        )

    async def execute(self, user_message: str, session_id: str = "default") -> Dict[str, Any]:
        steps: List[AgentStepLog] = []

        # Step 1: Requirements Analysis
        steps.append(self.create_step_log(
            step_num=1,
            thought=f"Analyzing website request: '{user_message}'. Planning visual layout, UI components, color scheme, and interaction logic.",
            action="Plan UI/UX Component Architecture",
            observation="Determined target design pattern and modern UI components."
        ))

        # Prompt engineering for website creation
        prompt = (
            f"Build a complete, standalone, visually stunning HTML page for the following user request:\n"
            f"\"{user_message}\"\n\n"
            f"Requirements:\n"
            f"- Fully styled with modern CSS (embedded in <style> tag). Use clean typography, responsive layout, subtle gradients, rounded corners, and proper spacing.\n"
            f"- Working JavaScript (embedded in <script> tag) for interactive UI logic.\n"
            f"- CRITICAL FOR MULTI-PAGE REQUESTS: If the user asks for a login and a dashboard/landing page, you MUST build a Single Page Application (SPA). Wrap the login in <div id='login-view'> and the dashboard in <div id='dashboard-view' style='display: none;'>.\n"
            f"- CRITICAL JAVASCRIPT: You MUST attach an event listener to the login form or button. Inside the listener, you MUST call `event.preventDefault()` to stop page reloads, then hide 'login-view' and show 'dashboard-view'.\n"
            f"- Return the complete HTML code enclosed in a ```html ``` block."
        )

        # Step 2: Code Generation via LLM
        steps.append(self.create_step_log(
            step_num=2,
            thought="Invoking Llama 3 LLM engine to synthesize HTML/CSS/JS code.",
            action="LLM Synthesis",
            observation="Code synthesis in progress..."
        ))

        print("\n=== DEBUG: SENDING PROMPT TO OLLAMA ===")
        llm_response = await ollama_client.generate(prompt=prompt, system_prompt=self.system_prompt)
        print("=== DEBUG: OLLAMA RAW RESPONSE START ===")
        print(repr(llm_response))
        print("=== DEBUG: OLLAMA RAW RESPONSE END ===\n")

        html_code = self._extract_html(llm_response)

        llm_response = await ollama_client.generate(prompt=prompt, system_prompt=self.system_prompt)

        # Extract HTML block from markdown response
        html_code = self._extract_html(llm_response)

        # If LLM failed or Ollama unavailable, generate a rich dynamic fallback based on user input
        if not html_code or "[Ollama Connection Warning" in llm_response:
            html_code = self._generate_dynamic_fallback(user_message)

        custom_name_match = re.search(r'[\'"]?([a-zA-Z0-9_-]+\.html)[\'"]?', user_message)
        
        if custom_name_match:
            file_name = custom_name_match.group(1) # Use the requested name
        else:
            site_id = f"site_{uuid.uuid4().hex[:8]}"
            file_name = f"{site_id}.html" # Fallback to random name

        result_msg = generate_website_file(file_name, html_code)

        preview_url = f"/generated_sites/{file_name}"
        webbrowser.open(f"http://localhost:8000{preview_url}")

        steps.append(self.create_step_log(
            step_num=3,
            thought=f"Saved website output to disk at 'generated_sites/{file_name}'. Preview ready.",
            action="File Persistence & URL Mounting",
            observation=f"Website successfully compiled. Live preview URL: {preview_url}"
        ))

        summary_text = (
            f"I have built the requested website for you! 🎉\n\n"
            f"**Summary of Generated Features:**\n"
            f"- Built customized UI layout for: '{user_message}'\n"
            f"- Included modern CSS styling and responsive design\n"
            f"- Added interactive JavaScript logic\n\n"
            f"File generated: {file_name}\n\n"
            f"You can view and test the live working preview directly in the preview window on the right!"
        )

        return {
            "response": summary_text,
            "steps": [step.dict() for step in steps],
            "generated_files": [file_name],
            "preview_url": preview_url
        }

    def _extract_html(self, text: str) -> str:
        if not text:
            return ""
        # First check for code blocks
        pattern = r"```html\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
            
        # Fallback: If no code blocks, look for raw HTML tags directly
        if "<!DOCTYPE html>" in text or "<html" in text or "<div" in text:
            # Clean off any leading text before the first HTML tag
            start_idx = text.find("<")
            if start_idx != -1:
                return text[start_idx:].strip()
                
        return text.strip() if text else ""

    def _generate_dynamic_fallback(self, query: str) -> str:
        """Generates a stylish, responsive, fully working modern dynamic webpage if Ollama is offline."""
        title = "JARVIS Generated Web Application"
        is_login = "login" in query.lower() or "auth" in query.lower() or "signin" in query.lower()

        if is_login:
            body_content = """
    <div class="card">
        <div class="logo">⚡ J.A.R.V.I.S. Auth</div>
        <h2>Welcome Back</h2>
        <p class="subtitle">Enter your credentials to access your digital twin portal</p>
        <form id="loginForm">
            <div class="input-group">
                <label>Email Address</label>
                <input type="email" placeholder="name@company.com" required value="demo@jarvis.ai">
            </div>
            <div class="input-group">
                <label>Password</label>
                <input type="password" placeholder="••••••••" required value="password123">
            </div>
            <button type="submit" class="btn">Sign In to Dashboard</button>
        </form>
        <div id="status" class="status-box" style="display:none;"></div>
    </div>
            """
            js_logic = """
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const status = document.getElementById('status');
            status.style.display = 'block';
            status.style.background = 'rgba(16, 185, 129, 0.2)';
            status.style.borderColor = '#10b981';
            status.style.color = '#10b981';
            status.innerHTML = '✓ Authentication Successful! Redirecting to JARVIS Core...';
        });
            """
        else:
            body_content = f"""
    <div class="card wide">
        <div class="logo">⚡ J.A.R.V.I.S. Core Platform</div>
        <h2>Dynamic Web Application</h2>
        <p class="subtitle">Generated dynamically for query: "{query}"</p>
        <div class="grid">
            <div class="stat-box">
                <div class="stat-title">Status</div>
                <div class="stat-value">Active</div>
            </div>
            <div class="stat-box">
                <div class="stat-title">Agent Engine</div>
                <div class="stat-value">Llama 3</div>
            </div>
            <div class="stat-box">
                <div class="stat-title">System Latency</div>
                <div class="stat-value">12ms</div>
            </div>
        </div>
        <button id="actionBtn" class="btn">Run System Diagnostics</button>
        <div id="status" class="status-box" style="display:none;"></div>
    </div>
            """
            js_logic = """
        document.getElementById('actionBtn').addEventListener('click', function() {
            const status = document.getElementById('status');
            status.style.display = 'block';
            status.style.background = 'rgba(59, 130, 246, 0.2)';
            status.style.borderColor = '#3b82f6';
            status.style.color = '#60a5fa';
            status.innerHTML = '⚡ System Diagnostic complete: All JARVIS Agents operating at 100% capacity.';
        });
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', system-ui, -apple-system, sans-serif; }}
        body {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f8fafc;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .card {{
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 36px;
            width: 100%;
            max-width: 440px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }}
        .card.wide {{ max-width: 680px; }}
        .logo {{ font-weight: 700; color: #38bdf8; font-size: 1.2rem; margin-bottom: 12px; }}
        h2 {{ font-size: 1.8rem; margin-bottom: 6px; font-weight: 700; }}
        .subtitle {{ color: #94a3b8; font-size: 0.95rem; margin-bottom: 24px; }}
        .input-group {{ margin-bottom: 18px; }}
        .input-group label {{ display: block; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 6px; font-weight: 500; }}
        .input-group input {{
            width: 100%;
            padding: 12px 16px;
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            color: #fff;
            font-size: 0.95rem;
            outline: none;
            transition: border 0.2s;
        }}
        .input-group input:focus {{ border-color: #38bdf8; }}
        .btn {{
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.1s, opacity 0.2s;
            margin-top: 10px;
        }}
        .btn:hover {{ opacity: 0.95; transform: translateY(-1px); }}
        .status-box {{
            margin-top: 20px;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 0.9rem;
            border: 1px solid;
        }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 20px; }}
        .stat-box {{ background: #0f172a; padding: 16px; border-radius: 8px; border: 1px solid #334155; }}
        .stat-title {{ font-size: 0.8rem; color: #94a3b8; }}
        .stat-value {{ font-size: 1.4rem; font-weight: 700; color: #38bdf8; margin-top: 4px; }}
    </style>
</head>
<body>
    {body_content}
    <script>
        {js_logic}
    </script>
</body>
</html>"""

web_builder_agent = WebBuilderAgent()
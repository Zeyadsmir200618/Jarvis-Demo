J.A.R.V.I.S. AI Twin (DEMO) ⚡ 
A fully autonomous, 1-click deployable Multi-Agent Digital Twin powered by local LLMs (Llama 3.2). J.A.R.V.I.S. features intelligent agent routing, live zero-dependency web UI generation, and system root-cause analysis—all running 100% locally on your own hardware without relying on cloud APIs.

🚀 Features
Local-First AI Execution: Powered by Ollama and Llama 3.2, running directly on your local GPU (optimized for 4GB+ VRAM like the RTX 3050) for maximum privacy and zero API costs.

Intelligent Agent Routing: Automatically categorizes user intents and routes them to specialized AI agents, or allows manual override via the UI.

Live Interactive Web Preview: The Web Builder Agent writes pure HTML/CSS/JS and instantly renders the result in a sandboxed Next.js iframe—bypassing the need for manual file rendering.

Root Cause Analysis (RCA): Paste raw error logs or stack traces, and the specialized RCA agent will diagnose the exact failure point and recommend structural fixes.

1-Click Orchestration: Spin up the entire microservice architecture (Ollama engine, Python backend, React frontend) via a single Windows batch script (start_jarvis.bat).

🏗️ Architecture & Tech Stack
J.A.R.V.I.S. is built on a modern microservices architecture to ensure non-blocking generation and high responsiveness.

Frontend: Next.js (React), Tailwind CSS, TypeScript.

Backend: FastAPI (Python), HTTPX (asynchronous LLM streaming), Pydantic.

AI Engine: Ollama (Llama 3.2 3B model) bound locally to 127.0.0.1:11434.

🛠️ Prerequisites
Before installing, ensure your system has the following installed:

Node.js (v18.0 or higher)

Python (v3.10 or higher)

Ollama (Windows installation)

Hardware: Dedicated GPU recommended (e.g., NVIDIA RTX 3050 4GB or better) for acceptable inference speeds.

⚙️ Quick Start
1. Prepare the AI Model
Open a terminal and pull the optimized Llama model into your local machine:

Bash
ollama pull llama3.2
2. Install Dependencies
You will need to install the dependencies for both the frontend and backend.

Bash
# Backend setup
cd backend
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
3. Launch J.A.R.V.I.S.
Return to the root directory and double-click the startup script:

Bash
start_jarvis.bat
This script will automatically open three synchronized terminal windows:

Ollama Engine - Serves the local LLM API.

JARVIS Backend - Runs the FastAPI server on [http://127.0.0.1:8000](http://127.0.0.1:8000).

JARVIS Frontend - Runs the Next.js development server on http://localhost:3000.

Note: To safely shut down all microservices and free up system ports, simply run stop_jarvis.bat.

🤖 Meet the Agents
J.A.R.V.I.S. utilizes a modular agent architecture to handle different tasks efficiently:

General Companion Agent: Handles standard conversational queries, brainstorming, and general knowledge.

Web & Code Builder Agent: Specialized in writing clean, single-file HTML/CSS/JS web applications. It outputs strictly formatted code blocks that the backend extracts and saves as .html files for the frontend to render live.

Root Cause Analysis (RCA) Agent: A strict, highly logical agent (running at a low temperature) designed to read system logs, identify port conflicts, trace Python exceptions, and provide precise, actionable fixes.

⚠️ Troubleshooting
1. "Only one usage of each socket address is normally permitted"

Cause: Ollama is already running silently in the Windows background tray, blocking port 11434.

Fix: Check your Windows system tray (bottom right corner), right-click the Ollama icon, and select "Quit". Then run start_jarvis.bat again.

2. Frontend stuck on "Orchestrator reasoning..." or Backend Timeout

Cause: Generating complete websites locally takes time. If the request takes longer than 5 minutes, standard browser fetch requests or HTTPX clients may time out.

Fix: Ensure the backend httpx.AsyncClient has timeout=None configured in ollama_client.py, and the frontend fetch call utilizes an extended AbortController signal. (These patches are included in the current stable build).

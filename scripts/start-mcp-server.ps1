# Start the J.A.R.V.I.S. host MCP server on Windows (PowerShell).
# First time:  python -m venv mcp-server\.venv ; mcp-server\.venv\Scripts\pip install -r mcp-server\requirements.txt
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repo "mcp-server\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
Push-Location (Join-Path $repo "mcp-server")
try { & $py -m jarvis_mcp_server --transport http } finally { Pop-Location }

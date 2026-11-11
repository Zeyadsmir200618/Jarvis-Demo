#!/usr/bin/env sh
# Start the J.A.R.V.I.S. host MCP server on macOS/Linux.
# First time:  python3 -m venv mcp-server/.venv && mcp-server/.venv/bin/pip install -r mcp-server/requirements.txt
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PY="$REPO/mcp-server/.venv/bin/python"; [ -x "$PY" ] || PY=python3
cd "$REPO/mcp-server" && exec "$PY" -m jarvis_mcp_server --transport http

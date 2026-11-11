"""MCP client used by the J.A.R.V.I.S. backend to reach the HOST workspace server.

Transports
  http  : Streamable HTTP to the host server (default; works from Docker via
          host.docker.internal). Authenticated with a bearer token.
  stdio : the backend spawns the server as a subprocess (only when the backend
          itself runs on the host, e.g. during development without Docker).

A fresh session is opened per call: simple, robust to server restarts, and
cheap at demo scale.
"""
from __future__ import annotations

import json
import shlex
from contextlib import asynccontextmanager
from typing import Any

import httpx
from mcp import ClientSession

from app.core import config


class MCPUnavailable(RuntimeError):
    pass


class MCPClient:
    @property
    def enabled(self) -> bool:
        return bool(config.MCP_SERVER_URL) if config.MCP_TRANSPORT == "http" else bool(config.MCP_STDIO_COMMAND)

    @asynccontextmanager
    async def session(self):
        if not self.enabled:
            raise MCPUnavailable("MCP is not configured (set MCP_SERVER_URL or MCP_STDIO_COMMAND).")
        try:
            if config.MCP_TRANSPORT == "stdio":
                from mcp import StdioServerParameters
                from mcp.client.stdio import stdio_client
                parts = shlex.split(config.MCP_STDIO_COMMAND)
                params = StdioServerParameters(command=parts[0], args=parts[1:])
                async with stdio_client(params) as (r, w):
                    async with ClientSession(r, w) as s:
                        await s.initialize()
                        yield s
            else:
                from mcp.client.streamable_http import streamable_http_client
                headers = {"Authorization": f"Bearer {config.MCP_AUTH_TOKEN}"}
                async with httpx.AsyncClient(headers=headers, timeout=httpx.Timeout(60, read=900)) as http:
                    async with streamable_http_client(config.MCP_SERVER_URL, http_client=http) as (r, w, _):
                        async with ClientSession(r, w) as s:
                            await s.initialize()
                            yield s
        except MCPUnavailable:
            raise
        except Exception as exc:  # connection refused, 401, DNS, ...
            raise MCPUnavailable(f"Cannot reach the MCP server: {type(exc).__name__}") from exc

    async def call(self, tool: str, args: dict[str, Any] | None = None) -> dict:
        async with self.session() as s:
            res = await s.call_tool(tool, args or {})
        text = "".join(getattr(c, "text", "") for c in res.content)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"ok": not res.isError, "text": text}
        if res.isError:
            data.setdefault("ok", False)
        return data

    async def describe(self) -> dict:
        async with self.session() as s:
            tools = (await s.list_tools()).tools
            resources = (await s.list_resources()).resources
            info = s.get_server_capabilities() if hasattr(s, "get_server_capabilities") else None
        return {"tools": [t.name for t in tools], "resources": [str(r.uri) for r in resources],
                "capabilities": bool(info)}


mcp_client = MCPClient()

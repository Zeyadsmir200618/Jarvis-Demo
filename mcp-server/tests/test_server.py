"""Policy unit tests + a real MCP round trip over Streamable HTTP (no mocks)."""
import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jarvis_mcp_server.approval import ApprovalVerifier, content_digest, mint_token  # noqa: E402
from jarvis_mcp_server.policy import Policy, PolicyError, redact  # noqa: E402

SECRET = "test-approval-secret-1234567890"
TOKEN = "test-bearer-token-abcdefghijkl"
DEMO = ROOT.parent / "sample-data" / "demo-project"


@pytest.fixture()
def project(tmp_path):
    dst = tmp_path / "demo-project"
    shutil.copytree(DEMO, dst)
    (dst / ".env").write_text("API_KEY=super-secret-value\n")
    (tmp_path / "outside.txt").write_text("outside")
    return dst


# ------------------------------------------------------------------ policy
def test_policy_blocks_escape_and_secrets(project):
    p = Policy.from_root(str(project))
    assert p.resolve("app.py").name == "app.py"
    for bad in ["../outside.txt", "/etc/passwd", "C:/Windows/win.ini", ".env", ".git/config", "keys/server.pem"]:
        with pytest.raises(PolicyError):
            p.resolve(bad)
    assert p.resolve(".env.example").name == ".env.example"


def test_policy_blocks_symlink_escape(project):
    try:
        (project / "link").symlink_to(project.parent / "outside.txt")
    except OSError:
        pytest.skip("symlinks not permitted on this OS")
    with pytest.raises(PolicyError):
        Policy.from_root(str(project)).resolve("link")


def test_policy_refuses_filesystem_root():
    with pytest.raises(PolicyError):
        Policy.from_root(Path.cwd().anchor)


def test_approval_token_binding():
    v = ApprovalVerifier(SECRET)
    d = content_digest("x")
    tok = mint_token(SECRET, "write", "app.py", d)
    with pytest.raises(PermissionError):
        v.verify(tok, "write", "other.py", d)          # wrong target
    v.verify(tok, "write", "app.py", d)                # correct
    with pytest.raises(PermissionError):
        v.verify(tok, "write", "app.py", d)            # replay
    with pytest.raises(PermissionError):
        v.verify(mint_token("wrong-secret-xxxxxxxxxx", "write", "app.py", d), "write", "app.py", d)
    with pytest.raises(PermissionError):
        v.verify(mint_token(SECRET, "write", "app.py", d, ttl=-1), "write", "app.py", d)


def test_redact():
    out = redact("API_KEY=abc123 token: zzz PASSWORD=hunter2 my-raw-secret", ["my-raw-secret"])
    assert "abc123" not in out and "hunter2" not in out and "my-raw-secret" not in out


# ------------------------------------------------------------------ real MCP over HTTP
def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close(); return port


@pytest.fixture()
def server(project):
    port = _free_port()
    env = {**os.environ, "JARVIS_APPROVAL_SECRET": SECRET, "MCP_AUTH_TOKEN": TOKEN, "MCP_ALLOWED_ROOT": str(project)}
    proc = subprocess.Popen([sys.executable, "-m", "jarvis_mcp_server", "--port", str(port)], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close(); break
        except OSError:
            time.sleep(0.2)
    yield f"http://127.0.0.1:{port}/mcp", project
    proc.terminate(); proc.wait(5)


async def _call(url, name, args, token=TOKEN):
    async with streamablehttp_client(url, headers={"Authorization": f"Bearer {token}"}) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool(name, args)
            return json.loads(res.content[0].text)


async def _list(url):
    async with streamablehttp_client(url, headers={"Authorization": f"Bearer {TOKEN}"}) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = [t.name for t in (await s.list_tools()).tools]
            res = [str(x.uri) for x in (await s.list_resources()).resources]
            tree = (await s.read_resource("project://tree")).contents[0].text
            return tools, res, tree


def test_mcp_end_to_end(server):
    url, project = server
    tools, resources, tree = asyncio.run(_list(url))
    assert {"read_file", "write_file", "run_command", "preview_write"} <= set(tools)
    assert "project://tree" in resources and "app.py" in tree and ".env\n" not in tree + "\n"

    # read allowed, secrets / escape refused
    assert "def greeting" in asyncio.run(_call(url, "read_file", {"path": "app.py"}))["content"]
    assert not asyncio.run(_call(url, "read_file", {"path": ".env"}))["ok"]
    assert not asyncio.run(_call(url, "read_file", {"path": "../outside.txt"}))["ok"]

    # tests fail before the fix (read-only commands don't need approval; run_tests does)
    assert not asyncio.run(_call(url, "run_command", {"command_id": "run_tests"}))["ok"]  # no token -> refused
    tok = mint_token(SECRET, "exec", "run_tests", project.name)
    r = asyncio.run(_call(url, "run_command", {"command_id": "run_tests", "approval_token": tok}))
    assert r["exit_code"] == 1 and "1 failed" in r["output"]

    # write requires approval bound to exact content
    new = (project / "app.py").read_text().replace('return f"Hello, {name}"', 'return f"Hello, {name}!"')
    prev = asyncio.run(_call(url, "preview_write", {"path": "app.py", "content": new}))
    assert prev["changed"] and '+    return f"Hello, {name}!"' in prev["diff"]
    assert not asyncio.run(_call(url, "write_file", {"path": "app.py", "content": new}))["ok"]
    wtok = mint_token(SECRET, "write", "app.py", prev["digest"])
    assert asyncio.run(_call(url, "write_file", {"path": "app.py", "content": new, "approval_token": wtok}))["ok"]
    assert not asyncio.run(_call(url, "write_file", {"path": "app.py", "content": new, "approval_token": wtok}))["ok"]  # replay

    tok2 = mint_token(SECRET, "exec", "run_tests", project.name)
    r2 = asyncio.run(_call(url, "run_command", {"command_id": "run_tests", "approval_token": tok2}))
    assert r2["ok"] and "1 passed" in r2["output"]


def test_http_requires_bearer(server):
    url, _ = server
    with pytest.raises(Exception):
        asyncio.run(_call(url, "project_summary", {}, token="wrong-token-value-0000"))

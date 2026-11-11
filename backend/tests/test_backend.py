import asyncio
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.core import config  # noqa: E402
from app.main import app  # noqa: E402
from app.orchestrator.router import orchestrator  # noqa: E402

client = TestClient(app)


def test_health_and_agents_roster():
    assert client.get("/health").json() == {"status": "ok"}
    r = client.get("/agents").json()
    assert len(r["agents"]) == 9
    assert r["orchestrator"]["key"] == "orchestrator"
    assert {a["key"] for a in r["agents"]} == {"monitoring", "detection", "rca", "prediction", "knowledge",
                                               "remediation", "validation", "security", "execution"}
    assert [a["key"] for a in r["agents"] if a["status"] != "planned"] == ["rca"]


@pytest.mark.parametrize("msg,expected", [
    ("PaymentService crashed: connection pool exhausted", "rca"),
    ("Build me a login page for a bank", "web_builder"),   # used to be misrouted to RCA ("login" contains "log")
    ("Please inspect the project on my PC", "workspace"),
    ("Here are the logs from last night's outage", "rca"),
])
def test_router_keywords(msg, expected):
    assert asyncio.run(orchestrator.classify(msg)) == expected


def test_workspace_disabled_without_config(monkeypatch):
    monkeypatch.setattr(config, "MCP_SERVER_URL", "")
    assert client.get("/workspace/status").json()["connected"] is False


# --------------------------------------------------------------------------- real MCP integration
MCP_DIR = REPO / "mcp-server"
SECRET, TOKEN = "integration-secret-0123456789", "integration-bearer-0123456789"


@pytest.fixture()
def live_mcp(tmp_path, monkeypatch):
    if not MCP_DIR.exists():
        pytest.skip("mcp-server not present (e.g. inside the backend container)")
    proj = tmp_path / "demo-project"
    shutil.copytree(REPO / "sample-data" / "demo-project", proj)
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    env = {**os.environ, "JARVIS_APPROVAL_SECRET": SECRET, "MCP_AUTH_TOKEN": TOKEN, "MCP_ALLOWED_ROOT": str(proj)}
    proc = subprocess.Popen([sys.executable, "-m", "jarvis_mcp_server", "--port", str(port)], cwd=MCP_DIR, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close(); break
        except OSError:
            time.sleep(0.2)
    monkeypatch.setattr(config, "MCP_TRANSPORT", "http")
    monkeypatch.setattr(config, "MCP_SERVER_URL", f"http://127.0.0.1:{port}/mcp")
    monkeypatch.setattr(config, "MCP_AUTH_TOKEN", TOKEN)
    monkeypatch.setattr(config, "JARVIS_APPROVAL_SECRET", SECRET)
    monkeypatch.setattr(config, "AUDIT_LOG_PATH", tmp_path / "audit.jsonl")
    yield proj
    proc.terminate(); proc.wait(5)


def test_full_mcp_workflow(live_mcp):
    st = client.get("/workspace/status").json()
    assert st["connected"] and "write_file" in st["tools"] and st["project"] == "demo-project"

    # 1) inspect (read-only)
    assert "app.py" in client.post("/workspace/inspect", json={"question": "inspect the project"}).json()["answer"]

    # 2) tests need approval -> pending -> approve -> 1 failed
    p = client.post("/workspace/commands", json={"command_id": "run_tests"}).json()
    assert p["status"] == "pending"
    r = client.post(f"/workspace/approvals/{p['action']['id']}/approve", json={}).json()
    assert r["status"] == "approved" and "1 failed" in r["result"]["output"]

    # 3) propose an edit: NOTHING is written until approval
    a = client.post("/workspace/propose-edit", json={"path": "app.py", "find": 'return f"Hello, {name}"',
                                                     "replace": 'return f"Hello, {name}!"'}).json()
    assert a["status"] == "pending" and '+    return f"Hello, {name}!"' in a["preview"]
    assert 'return f"Hello, {name}"\n' in (live_mcp / "app.py").read_text()

    # a rejected action is never executed
    b = client.post("/workspace/propose-edit", json={"path": "app.py", "find": "import os", "replace": "import os  # x"}).json()
    assert client.post(f"/workspace/approvals/{b['id']}/reject", json={"comment": "not needed"}).json()["status"] == "rejected"
    assert "# x" not in (live_mcp / "app.py").read_text()

    # 4) approve the fix -> file written on the "host" project
    assert client.post(f"/workspace/approvals/{a['id']}/approve", json={}).json()["result"]["ok"]
    assert 'return f"Hello, {name}!"' in (live_mcp / "app.py").read_text()

    # 5) re-run tests -> pass
    p2 = client.post("/workspace/commands", json={"command_id": "run_tests"}).json()
    r2 = client.post(f"/workspace/approvals/{p2['action']['id']}/approve", json={}).json()
    assert r2["result"]["ok"] and "1 passed" in r2["result"]["output"]

    # 6) secrets and path escapes stay blocked through the whole stack
    bad = client.post("/workspace/propose-edit", json={"path": "../evil.py", "find": "a", "replace": "b"})
    assert bad.status_code == 400

    # audit trail recorded every decision
    events = [e["event"] for e in client.get("/workspace/audit").json()]
    assert events.count("approved") == 3 and "rejected" in events

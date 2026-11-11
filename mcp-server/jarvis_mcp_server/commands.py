"""Allow-listed commands. There is NO generic shell tool.

Commands are defined server-side (never by the client or by files inside the
project). Each runs with ``shell=False``, a fixed argument list, the
authorized project as working directory, a timeout, a scrubbed environment and
redacted, truncated output.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .policy import redact

MAX_OUTPUT_CHARS = 12_000
PASS_ENV = ["PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "HOME", "USERPROFILE",
            "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG", "LANG"]


@dataclass(frozen=True)
class CommandSpec:
    id: str
    argv: list[str]
    description: str
    requires_approval: bool
    timeout: int = 300


def default_commands() -> dict[str, CommandSpec]:
    py = sys.executable
    specs = [
        CommandSpec("run_tests", [py, "-m", "pytest", "-q", "--color=no"], "Run the project's pytest suite", True, 300),
        CommandSpec("compose_up", ["docker", "compose", "up", "-d", "--build"], "Build and start the project's Docker Compose services", True, 900),
        CommandSpec("compose_down", ["docker", "compose", "down"], "Stop and remove the project's Docker Compose services", True, 300),
        CommandSpec("compose_ps", ["docker", "compose", "ps"], "Show service status (read-only)", False, 60),
        CommandSpec("compose_logs", ["docker", "compose", "logs", "--tail", "60", "--no-color"], "Show recent service logs (read-only, redacted)", False, 60),
    ]
    return {s.id: s for s in specs}


def load_commands(path: str | None) -> dict[str, CommandSpec]:
    """Optional override file — must live OUTSIDE the authorized project."""
    if not path:
        return default_commands()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for item in data["commands"]:
        argv = [sys.executable if a == "{python}" else a for a in item["argv"]]
        out[item["id"]] = CommandSpec(item["id"], argv, item.get("description", ""), bool(item.get("requires_approval", True)), int(item.get("timeout", 300)))
    return out


def run(spec: CommandSpec, cwd: Path, secrets_to_hide: list[str]) -> dict:
    env = {k: os.environ[k] for k in PASS_ENV if k in os.environ}
    try:
        proc = subprocess.run(spec.argv, cwd=str(cwd), env=env, shell=False, capture_output=True,
                              text=True, timeout=spec.timeout, encoding="utf-8", errors="replace")
        out, code, timed_out = (proc.stdout or "") + (proc.stderr or ""), proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        out, code, timed_out = f"{exc.stdout or ''}{exc.stderr or ''}\n[timed out after {spec.timeout}s]", -1, True
    except FileNotFoundError:
        out, code, timed_out = f"Executable not found: {spec.argv[0]}. Is it installed and on PATH for the MCP server?", 127, False
    out = redact(out, secrets_to_hide)
    truncated = len(out) > MAX_OUTPUT_CHARS
    if truncated:
        out = out[-MAX_OUTPUT_CHARS:]
    return {"command_id": spec.id, "argv": [Path(spec.argv[0]).name, *spec.argv[1:]], "exit_code": code,
            "ok": code == 0, "timed_out": timed_out, "output": out, "truncated": truncated}

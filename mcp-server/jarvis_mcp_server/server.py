"""J.A.R.V.I.S. host MCP server.

Runs on the HOST PC (not in Docker) so it can reach ONE explicitly authorized
project directory and the host's Docker Engine. The J.A.R.V.I.S. backend is
the MCP client.

Tools
  read-only : project_summary, list_directory, read_file, find_files,
              preview_write, list_commands, run_command(read-only ids)
  gated     : write_file, run_command(gated ids)  -> need a human approval token
Resources
  project://tree, project://file/{path}
"""
from __future__ import annotations

import argparse
import difflib
import hmac
import logging
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from . import commands as cmd
from .approval import ApprovalVerifier, content_digest
from .policy import MAX_READ_BYTES, MAX_WRITE_BYTES, Policy, PolicyError

log = logging.getLogger("jarvis-mcp")

KEY_FILES = ["README.md", "pyproject.toml", "requirements.txt", "package.json", "Dockerfile",
             "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]


def build_server(policy: Policy, verifier: ApprovalVerifier, command_specs: dict[str, cmd.CommandSpec],
                 secrets_to_hide: list[str], host: str = "127.0.0.1", port: int = 8765) -> FastMCP:
    mcp = FastMCP(
        "jarvis-host-workspace",
        host=host,
        port=port,
        instructions="Least-privilege access to one authorized project directory. "
                     "Writes and environment-changing commands require a human approval token.",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[
                "127.0.0.1:8765",
                "localhost:8765",
                "host.docker.internal:8765",
            ],
        ),
    )
    def _err(e: Exception) -> dict:
        return {"ok": False, "error": str(e)}

    def _tree(base: Path, depth: int, max_entries: int = 300) -> list[str]:
        lines: list[str] = []

        def walk(d: Path, level: int):
            if len(lines) >= max_entries:
                return
            try:
                entries = sorted(d.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except OSError:
                return
            for p in entries:
                if not policy.is_visible(p) or p.name in {"node_modules", "__pycache__", ".next", ".venv", "venv", ".pytest_cache"}:
                    continue
                lines.append("  " * level + p.name + ("/" if p.is_dir() else ""))
                if p.is_dir() and level + 1 < depth:
                    walk(p, level + 1)
        walk(base, 0)
        return lines

    # ---------------------------------------------------------------- read
    @mcp.tool()
    def project_summary() -> dict:
        """Overview of the authorized project: name, tree (depth 3) and detected key files."""
        found = [f for f in KEY_FILES if (policy.root / f).is_file()]
        return {"ok": True, "project": policy.root.name, "tree": _tree(policy.root, 3), "key_files": found,
                "commands": sorted(command_specs)}

    @mcp.tool()
    def list_directory(path: str = ".") -> dict:
        """List one directory inside the authorized project (sensitive entries hidden)."""
        try:
            d = policy.resolve(path)
            if not d.is_dir():
                return _err(NotADirectoryError(path))
            items = [{"name": p.name, "type": "dir" if p.is_dir() else "file", "size": p.stat().st_size if p.is_file() else None}
                     for p in sorted(d.iterdir()) if policy.is_visible(p)]
            return {"ok": True, "path": policy.rel(d), "entries": items}
        except (PolicyError, OSError) as e:
            return _err(e)

    @mcp.tool()
    def read_file(path: str) -> dict:
        """Read a UTF-8 text file inside the authorized project (max 200 KB; secrets files blocked)."""
        try:
            f = policy.resolve(path)
            if not f.is_file():
                return _err(FileNotFoundError(path))
            if f.stat().st_size > MAX_READ_BYTES:
                return _err(ValueError(f"File larger than {MAX_READ_BYTES} bytes"))
            return {"ok": True, "path": policy.rel(f), "content": f.read_text(encoding="utf-8")}
        except UnicodeDecodeError:
            return _err(ValueError("Not a UTF-8 text file"))
        except (PolicyError, OSError) as e:
            return _err(e)

    @mcp.tool()
    def find_files(pattern: str = "*.py", max_results: int = 100) -> dict:
        """Find files by glob pattern (e.g. '*.py', 'tests/*.py') inside the authorized project."""
        if ".." in pattern or pattern.startswith(("/", "\\")):
            return _err(PolicyError("Pattern must stay inside the project"))
        out = []
        for p in policy.root.rglob(pattern):
            if p.is_file() and policy.is_visible(p) and not any(x in p.parts for x in ("node_modules", ".venv", "__pycache__")):
                out.append(policy.rel(p))
                if len(out) >= min(max_results, 500):
                    break
        return {"ok": True, "matches": out}

    @mcp.tool()
    def preview_write(path: str, content: str) -> dict:
        """Show the unified diff a write WOULD make. Never writes. Returns the content digest to approve."""
        try:
            f = policy.resolve(path, for_write=True)
            if len(content.encode("utf-8")) > MAX_WRITE_BYTES:
                return _err(ValueError("Content too large"))
            old = f.read_text(encoding="utf-8") if f.is_file() else ""
            rel = policy.rel(f)
            diff = "".join(difflib.unified_diff(old.splitlines(True), content.splitlines(True), f"a/{rel}", f"b/{rel}"))
            return {"ok": True, "path": rel, "is_new_file": not f.exists(), "diff": diff or "(no changes)",
                    "digest": content_digest(content), "changed": old != content}
        except (PolicyError, OSError, UnicodeDecodeError) as e:
            return _err(e)

    @mcp.tool()
    def list_commands() -> dict:
        """List the allow-listed commands and whether each needs human approval."""
        return {"ok": True, "commands": [{"id": s.id, "description": s.description, "requires_approval": s.requires_approval}
                                         for s in command_specs.values()]}

    # ---------------------------------------------------------------- gated
    @mcp.tool()
    def write_file(path: str, content: str, approval_token: str = "") -> dict:
        """Write a text file inside the authorized project. REQUIRES a human approval token for this exact path+content."""
        try:
            f = policy.resolve(path, for_write=True)
            rel = policy.rel(f)
            digest = content_digest(content)
            verifier.verify(approval_token, "write", rel, digest)
            if len(content.encode("utf-8")) > MAX_WRITE_BYTES:
                return _err(ValueError("Content too large"))
            f.parent.mkdir(parents=True, exist_ok=True)
            tmp = f.with_name(f".{f.name}.jarvis-tmp")
            tmp.write_text(content, encoding="utf-8", newline="")
            os.replace(tmp, f)
            log.info("write_file approved and applied: %s", rel)
            return {"ok": True, "path": rel, "bytes": len(content.encode("utf-8")), "digest": digest}
        except (PolicyError, PermissionError, OSError) as e:
            log.warning("write_file refused: %s", e)
            return _err(e)

    @mcp.tool()
    def run_command(command_id: str, approval_token: str = "") -> dict:
        """Run ONE allow-listed command in the authorized project. Environment-changing commands need an approval token."""
        spec = command_specs.get(command_id)
        if spec is None:
            return _err(PolicyError(f"Unknown command '{command_id}'. Allowed: {sorted(command_specs)}"))
        try:
            if spec.requires_approval:
                verifier.verify(approval_token, "exec", command_id, policy.root.name)
        except PermissionError as e:
            log.warning("run_command refused: %s", e)
            return _err(e)
        log.info("run_command: %s", command_id)
        return cmd.run(spec, policy.root, secrets_to_hide)

    # ---------------------------------------------------------------- resources
    @mcp.resource("project://tree")
    def project_tree() -> str:
        """Text tree of the authorized project (depth 4)."""
        return "\n".join([policy.root.name + "/"] + ["  " + line for line in _tree(policy.root, 4)])

    @mcp.resource("project://file/{path}")
    def project_file(path: str) -> str:
        """A text file from the authorized project (same policy as read_file)."""
        f = policy.resolve(path)
        return f.read_text(encoding="utf-8")

    return mcp


class BearerAuthASGI:
    """Rejects HTTP requests that lack the shared bearer token (constant-time compare)."""

    def __init__(self, app, token: str):
        self.app, self.token = app, token.encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers") or [])
            auth = headers.get(b"authorization", b"")
            if not (auth.startswith(b"Bearer ") and hmac.compare_digest(auth[7:], self.token)):
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"application/json")]})
                await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
                return
        await self.app(scope, receive, send)


def _load_env_file() -> None:
    """Load mcp-server/.env (if present) without overriding real environment variables."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.is_file():
        from dotenv import load_dotenv
        load_dotenv(env_path, override=False)
        root = os.getenv("MCP_ALLOWED_ROOT", "")
        if root and not Path(root).expanduser().is_absolute():   # relative paths are relative to mcp-server/
            os.environ["MCP_ALLOWED_ROOT"] = str((env_path.parent / root).resolve())


def main(argv: list[str] | None = None) -> None:
    _load_env_file()
    ap = argparse.ArgumentParser(description="J.A.R.V.I.S. host MCP server")
    ap.add_argument("--transport", choices=["http", "stdio"], default=os.getenv("MCP_TRANSPORT", "http"))
    ap.add_argument("--host", default=os.getenv("MCP_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.getenv("MCP_PORT", "8765")))
    ap.add_argument("--root", default=os.getenv("MCP_ALLOWED_ROOT", ""))
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    secret = os.getenv("JARVIS_APPROVAL_SECRET", "")
    token = os.getenv("MCP_AUTH_TOKEN", "")
    policy = Policy.from_root(args.root)
    verifier = ApprovalVerifier(secret)
    specs = cmd.load_commands(os.getenv("MCP_COMMANDS_FILE"))
    if os.getenv("MCP_COMMANDS_FILE"):
        cf = Path(os.environ["MCP_COMMANDS_FILE"]).resolve()
        if cf.is_relative_to(policy.root):
            raise SystemExit("MCP_COMMANDS_FILE must live outside the authorized project directory.")
    server = build_server(policy, verifier, specs, [secret, token], args.host, args.port)
    log.info("Authorized project root: %s", policy.root)
    log.info("Commands: %s", ", ".join(f"{k}{'*' if v.requires_approval else ''}" for k, v in specs.items()))

    if args.transport == "stdio":
        server.run("stdio")
        return
    if len(token) < 16:
        raise SystemExit("MCP_AUTH_TOKEN must be set (16+ chars) for the HTTP transport.")
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        log.warning("Listening on %s — make sure your firewall only allows Docker/WSL traffic.", args.host)
    import uvicorn
    app = BearerAuthASGI(server.streamable_http_app(), token)
    log.info("MCP endpoint: http://%s:%d/mcp (bearer auth required)", args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()

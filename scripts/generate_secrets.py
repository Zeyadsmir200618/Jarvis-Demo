"""Create .env and mcp-server/.env from the examples with matching random secrets.

Usage:  python scripts/generate_secrets.py [--root PATH_TO_AUTHORIZED_PROJECT]
Secrets are written to the two .env files (both git-ignored) and never printed.
"""
import argparse
import re
import secrets
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def fill(example: Path, target: Path, values: dict[str, str]) -> None:
    if target.exists():
        print(f"skip: {target.relative_to(REPO)} already exists (delete it to regenerate)")
        return
    text = example.read_text(encoding="utf-8")
    for key, val in values.items():
        text = re.sub(rf"^{key}=.*$", lambda _: f"{key}={val}", text, flags=re.M)
    target.write_text(text, encoding="utf-8")
    print(f"wrote: {target.relative_to(REPO)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", help="absolute path of the project folder J.A.R.V.I.S. may access")
    a = ap.parse_args()
    vals = {"MCP_AUTH_TOKEN": secrets.token_urlsafe(32), "JARVIS_APPROVAL_SECRET": secrets.token_urlsafe(32)}
    fill(REPO / ".env.example", REPO / ".env", vals)
    mvals = dict(vals)
    if a.root:
        mvals["MCP_ALLOWED_ROOT"] = str(Path(a.root).expanduser().resolve())
    fill(REPO / "mcp-server" / ".env.example", REPO / "mcp-server" / ".env", mvals)

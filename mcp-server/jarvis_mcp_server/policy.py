"""Least-privilege access policy for the J.A.R.V.I.S. host MCP server.

Every path a client sends is resolved against ONE explicitly authorized
project root. Anything that resolves outside that root (``..``, absolute
paths, symlinks pointing elsewhere) is rejected, and sensitive files are
never readable or writable even inside the root.
"""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

# Names/patterns that are never exposed, even inside the authorized root.
DENIED_PARTS = {".git", ".ssh", ".aws", ".gnupg", "secrets", ".jarvis-secrets"}
DENIED_FILE_PATTERNS = [
    ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa*", "id_ed25519*",
    "*.sqlite", "*.db", ".npmrc", ".pypirc", "credentials*",
]
ALLOWED_DESPITE_PATTERN = {".env.example"}
# Read-only (listing/reading allowed, writing never allowed).
WRITE_DENIED_PARTS = {"node_modules", ".venv", "venv", "__pycache__", ".next", "dist", "build"}

MAX_READ_BYTES = 200_000
MAX_WRITE_BYTES = 200_000


class PolicyError(PermissionError):
    """Raised when a request violates the access policy."""


@dataclass(frozen=True)
class Policy:
    root: Path

    @classmethod
    def from_root(cls, root: str) -> "Policy":
        if not root:
            raise PolicyError("MCP_ALLOWED_ROOT is not set; refusing to start without an explicit project directory.")
        p = Path(root).expanduser().resolve(strict=True)
        if not p.is_dir():
            raise PolicyError(f"Authorized root is not a directory: {p}")
        if p == Path(p.anchor):
            raise PolicyError("Refusing to authorize a filesystem root (e.g. / or C:\\).")
        return cls(root=p)

    # ------------------------------------------------------------------ paths
    def resolve(self, rel: str | None, *, for_write: bool = False) -> Path:
        rel = (rel or ".").strip()
        if "\x00" in rel:
            raise PolicyError("Invalid path.")
        candidate = Path(rel)
        if candidate.is_absolute() or re.match(r"^[A-Za-z]:", rel):
            raise PolicyError("Absolute paths are not allowed; use a path relative to the authorized project.")
        target = (self.root / candidate).resolve(strict=False)
        try:
            relative = target.relative_to(self.root)
        except ValueError as exc:
            raise PolicyError("Path escapes the authorized project directory.") from exc
        self._check_sensitive(relative, for_write=for_write)
        return target

    def rel(self, p: Path) -> str:
        return PurePosixPath(p.relative_to(self.root)).as_posix() or "."

    def is_visible(self, p: Path) -> bool:
        try:
            self._check_sensitive(p.resolve().relative_to(self.root), for_write=False)
            return True
        except (PolicyError, ValueError):
            return False

    @staticmethod
    def _check_sensitive(relative: Path, *, for_write: bool) -> None:
        parts = relative.parts
        for part in parts:
            if part in DENIED_PARTS:
                raise PolicyError(f"Access to '{part}' is not permitted by policy.")
            if for_write and part in WRITE_DENIED_PARTS:
                raise PolicyError(f"Writing inside '{part}' is not permitted by policy.")
        if parts:
            name = parts[-1]
            if name not in ALLOWED_DESPITE_PATTERN and any(fnmatch.fnmatch(name, pat) for pat in DENIED_FILE_PATTERNS):
                raise PolicyError(f"'{name}' matches a protected-file pattern and is not accessible.")


_SECRET_ASSIGN = re.compile(r"(?i)\b([A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|API[_-]?KEY)[A-Z0-9_]*)\s*([=:])\s*([^\s'\"]+)")


def redact(text: str, extra_secrets: list[str] | None = None) -> str:
    """Remove known secret values and obvious KEY=value secrets from output."""
    for s in extra_secrets or []:
        if s and len(s) >= 6:
            text = text.replace(s, "[REDACTED]")
    return _SECRET_ASSIGN.sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", text)

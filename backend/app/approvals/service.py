"""Human-in-the-Loop approval queue + append-only audit trail (prototype).

Every write or environment-changing command is first stored here as a
PENDING action. Only an explicit human decision through the API
(POST /approvals/{id}/approve) mints the one-time token the MCP server
requires. Every proposal and decision is appended to data/audit.jsonl.
"""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core import config


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ApprovalService:
    def __init__(self):
        self._pending: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def audit(self, event: str, **fields) -> None:
        rec = {"ts": _now(), "event": event, **{k: v for k, v in fields.items() if k not in {"content", "token"}}}
        with self._lock, open(config.AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    def create(self, kind: str, summary: str, payload: dict[str, Any], preview: str = "") -> dict:
        action = {"id": uuid.uuid4().hex[:12], "kind": kind, "summary": summary, "status": "pending",
                  "created_at": _now(), "preview": preview, "payload": payload, "result": None}
        with self._lock:
            self._pending[action["id"]] = action
        self.audit("proposed", action_id=action["id"], kind=kind, summary=summary)
        return self.public(action)

    def get(self, action_id: str) -> dict | None:
        return self._pending.get(action_id)

    def list(self) -> list[dict]:
        return [self.public(a) for a in sorted(self._pending.values(), key=lambda a: a["created_at"], reverse=True)]

    def decide(self, action_id: str, status: str, actor: str, comment: str = "", result: Any = None) -> dict:
        a = self._pending[action_id]
        a["status"], a["decided_at"], a["decided_by"], a["comment"], a["result"] = status, _now(), actor, comment, result
        self.audit(status, action_id=action_id, kind=a["kind"], summary=a["summary"], actor=actor, comment=comment,
                   ok=(result or {}).get("ok") if isinstance(result, dict) else None)
        return self.public(a)

    def recent_audit(self, limit: int = 50) -> list[dict]:
        if not config.AUDIT_LOG_PATH.exists():
            return []
        lines = config.AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()[-limit:]
        return [json.loads(x) for x in reversed(lines)]

    @staticmethod
    def public(a: dict) -> dict:
        return {k: v for k, v in a.items() if k != "payload"} | {"target": a["payload"].get("path") or a["payload"].get("command_id")}


approval_service = ApprovalService()

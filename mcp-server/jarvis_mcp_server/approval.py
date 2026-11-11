"""Approval tokens: the MCP server's second line of defense.

The J.A.R.V.I.S. backend only mints a token after a human clicks *Approve*
in the dashboard. A token is bound to ONE action (a specific file + content
hash, or a specific allow-listed command), expires quickly and can be used
only once. Without a valid token, write and execute tools refuse to run, so
even a misbehaving client or model cannot change files or start services.

Format:  base64url(payload) "." hex(HMAC-SHA256(secret, payload))
payload: action|target|digest|expires_unix|nonce
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import threading
import time

DEFAULT_TTL_SECONDS = 120


def content_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def mint_token(secret: str, action: str, target: str, digest: str, ttl: int = DEFAULT_TTL_SECONDS) -> str:
    """Used by the backend (and tests). Kept here so both sides share one format."""
    if not secret:
        raise ValueError("approval secret is empty")
    payload = "|".join([action, target, digest, str(int(time.time()) + ttl), secrets.token_hex(8)])
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=") + "." + sig


class ApprovalVerifier:
    def __init__(self, secret: str):
        if not secret or len(secret) < 16:
            raise ValueError("JARVIS_APPROVAL_SECRET must be set (at least 16 characters).")
        self._secret = secret.encode()
        self._used: dict[str, float] = {}
        self._lock = threading.Lock()

    def verify(self, token: str | None, action: str, target: str, digest: str) -> None:
        if not token:
            raise PermissionError("Human approval required: no approval token supplied.")
        try:
            b64, sig = token.rsplit(".", 1)
            payload = base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4)).decode()
            t_action, t_target, t_digest, t_exp, nonce = payload.split("|")
        except Exception as exc:  # noqa: BLE001
            raise PermissionError("Malformed approval token.") from exc
        expected = hmac.new(self._secret, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            raise PermissionError("Approval token signature is invalid.")
        if (t_action, t_target, t_digest) != (action, target, digest):
            raise PermissionError("Approval token does not match this exact action.")
        now = time.time()
        if int(t_exp) < now:
            raise PermissionError("Approval token has expired; approve the action again.")
        with self._lock:
            self._used = {n: e for n, e in self._used.items() if e > now}
            if nonce in self._used:
                raise PermissionError("Approval token was already used.")
            self._used[nonce] = float(t_exp)

"""Mints single-use approval tokens. Format must match mcp-server/jarvis_mcp_server/approval.py."""
import base64
import hashlib
import hmac
import secrets
import time


def mint_token(secret: str, action: str, target: str, digest: str, ttl: int = 120) -> str:
    if not secret or len(secret) < 16:
        raise RuntimeError("JARVIS_APPROVAL_SECRET is not configured (16+ characters).")
    payload = "|".join([action, target, digest, str(int(time.time()) + ttl), secrets.token_hex(8)])
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=") + "." + sig

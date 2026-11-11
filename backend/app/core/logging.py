"""Logging with secret redaction, so tokens never reach logs."""
import logging
import re

from app.core import config

_PATTERN = re.compile(r"(?i)\b([A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|API[_-]?KEY)[A-Z0-9_]*)\s*([=:])\s*([^\s'\"]+)")


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for s in (config.MCP_AUTH_TOKEN, config.JARVIS_APPROVAL_SECRET):
            if s:
                msg = msg.replace(s, "[REDACTED]")
        record.msg, record.args = _PATTERN.sub(r"\1\2[REDACTED]", msg), ()
        return True


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    for h in logging.getLogger().handlers:
        h.addFilter(RedactingFilter())

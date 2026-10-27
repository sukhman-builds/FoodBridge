"""Single source of "now" so tests can control time."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

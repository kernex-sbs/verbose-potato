"""Runtime configuration shared by CLI and HTTP entrypoints."""

from __future__ import annotations

import os


DATABASE_URL = os.environ.get(
    "EVALSTACK_DATABASE_URL",
    "postgresql://evalstack:evalstack@postgres:5432/evalstack",
)
REDIS_URL = os.environ.get("EVALSTACK_REDIS_URL", "redis://redis:6379/0")
HTTP_HOST = os.environ.get("EVALSTACK_HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.environ.get("EVALSTACK_HTTP_PORT", "8080"))

QUEUE_KEY = "evalstack:queue:seed-work"
RESULT_CACHE_PREFIX = "evalstack:cache:completed:"


def result_cache_key(checkpoint_content_ref: str, contract_content_ref: str) -> str:
    """Cache key keyed by content identity, not display labels.

    Two documents can share a display label (same run_id/checkpoint_name, or
    same suite_name) while differing in content; the cache must not conflate
    them, so it is always keyed by the content-addressed refs.
    """
    return f"{RESULT_CACHE_PREFIX}{checkpoint_content_ref}|{contract_content_ref}"

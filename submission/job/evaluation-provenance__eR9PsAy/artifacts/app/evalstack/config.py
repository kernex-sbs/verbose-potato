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

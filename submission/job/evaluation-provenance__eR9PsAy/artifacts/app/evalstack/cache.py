"""Disposable completed-result cache.

Keyed strictly by checkpoint/contract content refs, never by human labels,
so distinct content is never conflated (see SPEC.md provenance invariants).
Postgres `canonical_results` remains the durable authority: losing this
cache only costs a re-lookup, never correctness or re-evaluation.
"""

from __future__ import annotations

import json
from typing import Any

import psycopg
import redis

from .config import RESULT_CACHE_PREFIX
from .db import canonical_result


def _cache_key(checkpoint_ref: str, contract_ref: str) -> str:
    return f"{RESULT_CACHE_PREFIX}{checkpoint_ref}|{contract_ref}"


def cache_put_score(
    cache: redis.Redis, checkpoint_ref: str, contract_ref: str, score: int
) -> None:
    cache.set(
        _cache_key(checkpoint_ref, contract_ref),
        json.dumps({"score": score}, sort_keys=True),
    )


def resolve_canonical_score(
    conn: psycopg.Connection,
    cache: redis.Redis,
    checkpoint_ref: str,
    contract_ref: str,
) -> int | None:
    """Return the canonical score for this exact content pair, if any.

    Checks the disposable cache first, falling back to the durable
    Postgres table on a miss (and repopulating the cache from it).
    """
    raw = cache.get(_cache_key(checkpoint_ref, contract_ref))
    if raw is not None:
        return int(json.loads(raw)["score"])
    row = canonical_result(conn, checkpoint_ref, contract_ref)
    if row is None:
        return None
    score = int(row["score"])
    cache_put_score(cache, checkpoint_ref, contract_ref, score)
    return score

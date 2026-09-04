"""Inspection, metrics, and leaderboard projection."""

from __future__ import annotations

from typing import Any

from .config import RESULT_CACHE_PREFIX
from .db import active_contract, connection, redis_client


def clear_result_cache() -> dict[str, int]:
    client = redis_client()
    keys = list(client.scan_iter(match=f"{RESULT_CACHE_PREFIX}*"))
    deleted = int(client.delete(*keys)) if keys else 0
    return {"deleted": deleted}


def leaderboard() -> dict[str, Any]:
    """Project each candidate's current publication under the active contract.

    This intentionally never looks at the jobs table: job/submission/completion
    order must not affect what is "current". Only the append-only publications
    history (latest per candidate) and the content-keyed, durable
    canonical_results table matter.
    """
    with connection() as conn:
        active = active_contract(conn)
        active_ref = active["contract_content_ref"] if active else None
        publications = conn.execute(
            """
            SELECT DISTINCT ON (candidate_id)
                   candidate_id, publication_id, checkpoint_content_ref
            FROM publications
            ORDER BY candidate_id, publication_seq DESC
            """
        ).fetchall()
        entries: list[dict[str, Any]] = []
        for publication in publications:
            canonical = None
            if active_ref is not None:
                canonical = conn.execute(
                    """
                    SELECT score FROM canonical_results
                    WHERE checkpoint_content_ref = %s AND contract_content_ref = %s
                    """,
                    (publication["checkpoint_content_ref"], active_ref),
                ).fetchone()
            entries.append(
                {
                    "candidate_id": publication["candidate_id"],
                    "publication_id": publication["publication_id"],
                    "checkpoint_content_ref": publication["checkpoint_content_ref"],
                    "contract_content_ref": active_ref,
                    "status": "complete" if canonical is not None else "pending",
                    "score": int(canonical["score"]) if canonical is not None else None,
                }
            )
    return {
        "contract_content_ref": active_ref,
        "entries": entries,
    }


def inspect(candidate_id: str | None = None) -> dict[str, Any]:
    where = " WHERE candidate_id = %s" if candidate_id else ""
    params = (candidate_id,) if candidate_id else ()
    with connection() as conn:
        publications = conn.execute(
            "SELECT * FROM publications" + where + " ORDER BY publication_seq", params
        ).fetchall()
        jobs = conn.execute(
            "SELECT * FROM jobs" + where + " ORDER BY job_seq", params
        ).fetchall()
        activations = conn.execute(
            "SELECT * FROM contract_activations ORDER BY activation_seq"
        ).fetchall()
        seed_results = conn.execute(
            """
            SELECT checkpoint_content_ref, contract_content_ref, seed, score, source_job_id
            FROM seed_results
            ORDER BY checkpoint_content_ref, contract_content_ref, seed
            """
        ).fetchall()
        results = conn.execute(
            """
            SELECT checkpoint_content_ref, contract_content_ref, score, seed_count,
                   completed_by_job_id, completed_seq
            FROM canonical_results
            ORDER BY completed_seq
            """
        ).fetchall()
    return {
        "publications": publications,
        "activations": activations,
        "jobs": jobs,
        "seed_results": seed_results,
        "results": results,
    }


def metrics() -> dict[str, int]:
    with connection() as conn:
        names = {
            "evaluator_invocations": "evaluator_calls",
            "publication_count": "publications",
            "job_count": "jobs",
            "seed_result_count": "seed_results",
            "result_count": "canonical_results",
        }
        result: dict[str, int] = {}
        for key, table in names.items():
            row = conn.execute(f"SELECT count(*) AS value FROM {table}").fetchone()
            assert row is not None
            result[key] = int(row["value"])
        return result

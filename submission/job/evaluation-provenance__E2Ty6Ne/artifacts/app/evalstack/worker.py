"""Deterministic single-delivery evaluation worker."""

from __future__ import annotations

import json
from typing import Any

from .config import QUEUE_KEY, RESULT_CACHE_PREFIX
from .db import (
    checkpoint_document,
    connection,
    contract_document,
    next_identifier,
    redis_client,
)
from .evaluator import seed_score


def _cache_key(checkpoint_ref: str, contract_ref: str) -> str:
    return f"{RESULT_CACHE_PREFIX}{checkpoint_ref}|{contract_ref}"


def _finish_job(
    conn,
    job: dict[str, Any],
    checkpoint_ref: str,
    contract_ref: str,
    score: int,
    seed_count: int,
) -> int:
    existing = conn.execute(
        """
        SELECT completed_seq FROM canonical_results
        WHERE checkpoint_content_ref = %s AND contract_content_ref = %s
        """,
        (checkpoint_ref, contract_ref),
    ).fetchone()
    if existing is None:
        _, result_completion_seq = next_identifier(conn, "completion")
        conn.execute(
            """
            INSERT INTO canonical_results(
                checkpoint_content_ref, contract_content_ref, score, seed_count,
                completed_by_job_id, completed_seq
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                checkpoint_ref,
                contract_ref,
                score,
                seed_count,
                job["job_id"],
                result_completion_seq,
            ),
        )
    _, job_completion_seq = next_identifier(conn, "completion")
    conn.execute(
        """
        UPDATE jobs
        SET status = 'complete', resolved_checkpoint_content_ref = %s,
            resolved_contract_content_ref = %s, completed_seq = %s
        WHERE job_id = %s
        """,
        (checkpoint_ref, contract_ref, job_completion_seq, job["job_id"]),
    )
    return job_completion_seq


def process_one() -> dict[str, Any]:
    cache = redis_client()
    raw = cache.lpop(QUEUE_KEY)
    if raw is None:
        return {"status": "empty"}
    delivery = json.loads(raw)
    job_id = delivery["job_id"]
    forced_seed = delivery.get("seed")

    with connection() as conn:
        job = conn.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,)).fetchone()
        if job is None:
            raise ValueError(f"unknown queued job: {job_id}")

        # Use the checkpoint/contract snapshot recorded when the job was
        # accepted, never the candidate's or contract's current state.
        checkpoint_ref = job["checkpoint_content_ref"]
        contract_ref = job["contract_content_ref"]
        checkpoint = checkpoint_document(conn, checkpoint_ref)
        contract_document_value = contract_document(conn, contract_ref)

        complete = conn.execute(
            """
            SELECT score, seed_count FROM canonical_results
            WHERE checkpoint_content_ref = %s AND contract_content_ref = %s
            """,
            (checkpoint_ref, contract_ref),
        ).fetchone()
        if complete is not None:
            _finish_job(
                conn,
                job,
                checkpoint_ref,
                contract_ref,
                int(complete["score"]),
                int(complete["seed_count"]),
            )
            cache.set(
                _cache_key(checkpoint_ref, contract_ref),
                json.dumps(
                    {
                        "checkpoint_content_ref": checkpoint_ref,
                        "contract_content_ref": contract_ref,
                        "score": int(complete["score"]),
                    },
                    sort_keys=True,
                ),
            )
            return {
                "status": "complete",
                "job_id": job_id,
                "seed": forced_seed,
                "checkpoint_content_ref": checkpoint_ref,
                "contract_content_ref": contract_ref,
                "score": int(complete["score"]),
            }

        seeds = [int(entry["seed"]) for entry in contract_document_value["seeds"]]
        if forced_seed is not None:
            seed = int(forced_seed)
            if seed not in seeds:
                raise ValueError(f"seed {seed} is not in the current contract")
        else:
            completed_seeds = {
                int(row["seed"])
                for row in conn.execute(
                    """
                    SELECT seed FROM seed_results
                    WHERE checkpoint_content_ref = %s AND contract_content_ref = %s
                    """,
                    (checkpoint_ref, contract_ref),
                ).fetchall()
            }
            seed = next((value for value in seeds if value not in completed_seeds), seeds[0])

        duplicate = conn.execute(
            """
            SELECT score FROM seed_results
            WHERE checkpoint_content_ref = %s AND contract_content_ref = %s AND seed = %s
            """,
            (checkpoint_ref, contract_ref, seed),
        ).fetchone()
        conn.execute("UPDATE jobs SET status = 'running' WHERE job_id = %s", (job_id,))
        if duplicate is None:
            score = seed_score(checkpoint, contract_document_value, seed)
            conn.execute(
                """
                INSERT INTO evaluator_calls(
                    checkpoint_content_ref, contract_content_ref, seed, job_id
                ) VALUES (%s, %s, %s, %s)
                """,
                (checkpoint_ref, contract_ref, seed, job_id),
            )
            conn.execute(
                """
                INSERT INTO seed_results(
                    checkpoint_content_ref, contract_content_ref, seed, score, source_job_id
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (checkpoint_ref, contract_ref, seed, score, job_id),
            )
            outcome = "processed"
        else:
            score = int(duplicate["score"])
            outcome = "duplicate"

        rows = conn.execute(
            """
            SELECT seed, score FROM seed_results
            WHERE checkpoint_content_ref = %s AND contract_content_ref = %s
            """,
            (checkpoint_ref, contract_ref),
        ).fetchall()
        scores = {int(row["seed"]): int(row["score"]) for row in rows}
        if all(value in scores for value in seeds):
            total = sum(scores[value] for value in seeds)
            _finish_job(conn, job, checkpoint_ref, contract_ref, total, len(seeds))
            cache.set(
                _cache_key(checkpoint_ref, contract_ref),
                json.dumps(
                    {
                        "checkpoint_content_ref": checkpoint_ref,
                        "contract_content_ref": contract_ref,
                        "score": total,
                    },
                    sort_keys=True,
                ),
            )
            outcome = "complete"
            result_score: int | None = total
        else:
            cache.rpush(QUEUE_KEY, json.dumps({"job_id": job_id}, sort_keys=True))
            result_score = None

    return {
        "status": outcome,
        "job_id": job_id,
        "seed": seed,
        "checkpoint_content_ref": checkpoint_ref,
        "contract_content_ref": contract_ref,
        "score": result_score,
    }

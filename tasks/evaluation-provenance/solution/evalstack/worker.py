"""Deterministic worker carrying accepted provenance through every delivery."""

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


def _cache_result(
    checkpoint_ref: str, contract_ref: str, score: int
) -> None:
    redis_client().set(
        _cache_key(checkpoint_ref, contract_ref),
        json.dumps(
            {
                "checkpoint_content_ref": checkpoint_ref,
                "contract_content_ref": contract_ref,
                "score": score,
            },
            sort_keys=True,
        ),
    )


def _complete_job(
    conn,
    job: dict[str, Any],
    checkpoint_ref: str,
    contract_ref: str,
    score: int,
    seed_count: int,
) -> None:
    result = conn.execute(
        """
        SELECT score FROM canonical_results
        WHERE checkpoint_content_ref = %s AND contract_content_ref = %s
        """,
        (checkpoint_ref, contract_ref),
    ).fetchone()
    if result is None:
        _, result_seq = next_identifier(conn, "completion")
        conn.execute(
            """
            INSERT INTO canonical_results(
                checkpoint_content_ref, contract_content_ref, score, seed_count,
                completed_by_job_id, completed_seq
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (checkpoint_content_ref, contract_content_ref) DO NOTHING
            """,
            (checkpoint_ref, contract_ref, score, seed_count, job["job_id"], result_seq),
        )
    _, job_seq = next_identifier(conn, "completion")
    conn.execute(
        """
        UPDATE jobs
        SET status = 'complete', resolved_checkpoint_content_ref = %s,
            resolved_contract_content_ref = %s, completed_seq = %s
        WHERE job_id = %s
        """,
        (checkpoint_ref, contract_ref, job_seq, job["job_id"]),
    )


def process_one() -> dict[str, Any]:
    client = redis_client()
    raw = client.lpop(QUEUE_KEY)
    if raw is None:
        return {"status": "empty"}
    delivery = json.loads(raw)
    job_id = delivery["job_id"]
    forced_seed = delivery.get("seed")

    with connection() as conn:
        job = conn.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,)).fetchone()
        if job is None:
            raise ValueError(f"unknown queued job: {job_id}")
        checkpoint_ref = job["checkpoint_content_ref"]
        contract_ref = job["contract_content_ref"]
        checkpoint = checkpoint_document(conn, checkpoint_ref)
        contract = contract_document(conn, contract_ref)
        seeds = [int(entry["seed"]) for entry in contract["seeds"]]

        canonical = conn.execute(
            """
            SELECT score, seed_count FROM canonical_results
            WHERE checkpoint_content_ref = %s AND contract_content_ref = %s
            """,
            (checkpoint_ref, contract_ref),
        ).fetchone()
        if canonical is not None:
            score = int(canonical["score"])
            _complete_job(
                conn,
                job,
                checkpoint_ref,
                contract_ref,
                score,
                int(canonical["seed_count"]),
            )
            outcome = {
                "status": "complete",
                "job_id": job_id,
                "seed": int(forced_seed) if forced_seed is not None else None,
                "checkpoint_content_ref": checkpoint_ref,
                "contract_content_ref": contract_ref,
                "score": score,
            }
        else:
            rows = conn.execute(
                """
                SELECT seed, score FROM seed_results
                WHERE checkpoint_content_ref = %s AND contract_content_ref = %s
                """,
                (checkpoint_ref, contract_ref),
            ).fetchall()
            completed = {int(row["seed"]): int(row["score"]) for row in rows}
            if forced_seed is not None:
                seed = int(forced_seed)
                if seed not in seeds:
                    raise ValueError(f"seed {seed} is not in the accepted contract")
            else:
                seed = next((value for value in seeds if value not in completed), seeds[0])

            if seed in completed:
                seed_value = completed[seed]
                status = "duplicate"
            else:
                seed_value = seed_score(checkpoint, contract, seed)
                conn.execute(
                    """
                    INSERT INTO evaluator_calls(
                        checkpoint_content_ref, contract_content_ref, seed, job_id
                    ) VALUES (%s, %s, %s, %s)
                    """,
                    (checkpoint_ref, contract_ref, seed, job_id),
                )
                inserted = conn.execute(
                    """
                    INSERT INTO seed_results(
                        checkpoint_content_ref, contract_content_ref, seed, score,
                        source_job_id
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (checkpoint_content_ref, contract_content_ref, seed)
                    DO NOTHING
                    RETURNING seed
                    """,
                    (checkpoint_ref, contract_ref, seed, seed_value, job_id),
                ).fetchone()
                status = "processed" if inserted is not None else "duplicate"
            conn.execute("UPDATE jobs SET status = 'running' WHERE job_id = %s", (job_id,))

            rows = conn.execute(
                """
                SELECT seed, score FROM seed_results
                WHERE checkpoint_content_ref = %s AND contract_content_ref = %s
                """,
                (checkpoint_ref, contract_ref),
            ).fetchall()
            completed = {int(row["seed"]): int(row["score"]) for row in rows}
            if all(value in completed for value in seeds):
                score = sum(completed[value] for value in seeds)
                _complete_job(
                    conn, job, checkpoint_ref, contract_ref, score, len(seeds)
                )
                status = "complete"
                result_score: int | None = score
            else:
                client.rpush(QUEUE_KEY, json.dumps({"job_id": job_id}, sort_keys=True))
                result_score = None
            outcome = {
                "status": status,
                "job_id": job_id,
                "seed": seed,
                "checkpoint_content_ref": checkpoint_ref,
                "contract_content_ref": contract_ref,
                "score": result_score,
            }

    if outcome["status"] == "complete":
        assert outcome["score"] is not None
        _cache_result(checkpoint_ref, contract_ref, int(outcome["score"]))
    return outcome

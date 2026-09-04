"""Publication, contract activation, and evaluation acceptance."""

from __future__ import annotations

import json
from typing import Any

from .config import QUEUE_KEY, result_cache_key
from .db import (
    active_contract,
    connection,
    current_publication,
    next_identifier,
    redis_client,
)
from .documents import (
    checkpoint_label,
    content_ref,
    contract_label,
    load_document,
    validate_checkpoint,
    validate_contract,
)


def publish(candidate_id: str, checkpoint_path: str) -> dict[str, Any]:
    if not candidate_id:
        raise ValueError("candidate_id must be non-empty")
    document = load_document(checkpoint_path)
    validate_checkpoint(document)
    ref = content_ref("checkpoint", document)
    label = checkpoint_label(document)
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO checkpoint_contents(checkpoint_content_ref, document)
            VALUES (%s, %s::jsonb)
            ON CONFLICT (checkpoint_content_ref) DO NOTHING
            """,
            (ref, json.dumps(document)),
        )
        publication_id, publication_seq = next_identifier(conn, "publication")
        conn.execute(
            """
            INSERT INTO publications(
                publication_id, publication_seq, candidate_id,
                checkpoint_content_ref, checkpoint_label
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (publication_id, publication_seq, candidate_id, ref, label),
        )
    return {
        "candidate_id": candidate_id,
        "publication_id": publication_id,
        "checkpoint_content_ref": ref,
    }


def activate_contract(contract_path: str) -> dict[str, Any]:
    document = load_document(contract_path)
    validate_contract(document)
    ref = content_ref("contract", document)
    label = contract_label(document)
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO contract_contents(contract_content_ref, document)
            VALUES (%s, %s::jsonb)
            ON CONFLICT (contract_content_ref) DO NOTHING
            """,
            (ref, json.dumps(document)),
        )
        activation_id, activation_seq = next_identifier(conn, "activation")
        conn.execute(
            """
            INSERT INTO contract_activations(
                activation_id, activation_seq, contract_content_ref, contract_label
            ) VALUES (%s, %s, %s, %s)
            """,
            (activation_id, activation_seq, ref, label),
        )
    return {"activation_id": activation_id, "contract_content_ref": ref}


def submit(candidate_id: str) -> dict[str, Any]:
    """Accept the current target and reuse completed work when available.

    Provenance identity is the (checkpoint_content_ref, contract_content_ref)
    pair. The Redis cache is a disposable accelerator in front of the durable
    Postgres canonical_results table: a cache miss falls back to Postgres so
    losing the cache never loses completed work or forces reevaluation.
    """
    cache = redis_client()
    with connection() as conn:
        publication = current_publication(conn, candidate_id)
        contract = active_contract(conn)
        if publication is None or contract is None:
            raise ValueError("candidate has no current publication or active contract")

        checkpoint_ref = publication["checkpoint_content_ref"]
        contract_ref = contract["contract_content_ref"]
        job_id, job_seq = next_identifier(conn, "job")

        cache_key = result_cache_key(checkpoint_ref, contract_ref)
        cached_raw = cache.get(cache_key)
        if cached_raw is not None:
            score = int(json.loads(cached_raw)["score"])
        else:
            existing = conn.execute(
                """
                SELECT score FROM canonical_results
                WHERE checkpoint_content_ref = %s AND contract_content_ref = %s
                """,
                (checkpoint_ref, contract_ref),
            ).fetchone()
            score = int(existing["score"]) if existing is not None else None
            if existing is not None:
                cache.set(cache_key, json.dumps({"score": score}, sort_keys=True))

        reused = score is not None
        status = "complete" if reused else "queued"
        completed_seq = None
        resolved_checkpoint = None
        resolved_contract = None
        if reused:
            _, completed_seq = next_identifier(conn, "completion")
            resolved_checkpoint = checkpoint_ref
            resolved_contract = contract_ref

        conn.execute(
            """
            INSERT INTO jobs(
                job_id, job_seq, candidate_id, publication_id,
                checkpoint_content_ref, contract_content_ref,
                checkpoint_label, contract_label, status, reused,
                resolved_checkpoint_content_ref, resolved_contract_content_ref,
                completed_seq
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                job_id,
                job_seq,
                candidate_id,
                publication["publication_id"],
                checkpoint_ref,
                contract_ref,
                publication["checkpoint_label"],
                contract["contract_label"],
                status,
                reused,
                resolved_checkpoint,
                resolved_contract,
                completed_seq,
            ),
        )

    if not reused:
        cache.rpush(QUEUE_KEY, json.dumps({"job_id": job_id}, sort_keys=True))
    return {
        "job_id": job_id,
        "candidate_id": candidate_id,
        "publication_id": publication["publication_id"],
        "checkpoint_content_ref": checkpoint_ref,
        "contract_content_ref": contract_ref,
        "status": status,
        "reused": reused,
    }


def retry_one(job_id: str, seed: int) -> dict[str, Any]:
    with connection() as conn:
        if conn.execute("SELECT 1 FROM jobs WHERE job_id = %s", (job_id,)).fetchone() is None:
            raise ValueError(f"unknown job: {job_id}")
    redis_client().rpush(
        QUEUE_KEY, json.dumps({"job_id": job_id, "seed": seed}, sort_keys=True)
    )
    return {"job_id": job_id, "seed": seed, "status": "queued"}

"""Publication, contract activation, and evaluation acceptance."""

from __future__ import annotations

import json
from typing import Any

from .config import QUEUE_KEY, RESULT_CACHE_PREFIX
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


def _cache_key(checkpoint_ref: str, contract_ref: str) -> str:
    return f"{RESULT_CACHE_PREFIX}{checkpoint_ref}|{contract_ref}"


def submit(candidate_id: str) -> dict[str, Any]:
    """Accept the current target and reuse completed work when available."""
    cache = redis_client()
    with connection() as conn:
        publication = current_publication(conn, candidate_id)
        contract = active_contract(conn)
        if publication is None or contract is None:
            raise ValueError("candidate has no current publication or active contract")

        job_id, job_seq = next_identifier(conn, "job")
        cached_raw = cache.get(
            _cache_key(
                publication["checkpoint_content_ref"], contract["contract_content_ref"]
            )
        )
        cached = json.loads(cached_raw) if cached_raw else None
        status = "complete" if cached else "queued"
        completed_seq = None
        resolved_checkpoint = None
        resolved_contract = None
        if cached:
            _, completed_seq = next_identifier(conn, "completion")
            resolved_checkpoint = cached["checkpoint_content_ref"]
            resolved_contract = cached["contract_content_ref"]

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
                publication["checkpoint_content_ref"],
                contract["contract_content_ref"],
                publication["checkpoint_label"],
                contract["contract_label"],
                status,
                bool(cached),
                resolved_checkpoint,
                resolved_contract,
                completed_seq,
            ),
        )

    if not cached:
        cache.rpush(QUEUE_KEY, json.dumps({"job_id": job_id}, sort_keys=True))
    return {
        "job_id": job_id,
        "candidate_id": candidate_id,
        "publication_id": publication["publication_id"],
        "checkpoint_content_ref": publication["checkpoint_content_ref"],
        "contract_content_ref": contract["contract_content_ref"],
        "status": status,
        "reused": bool(cached),
    }


def retry_one(job_id: str, seed: int) -> dict[str, Any]:
    with connection() as conn:
        if conn.execute("SELECT 1 FROM jobs WHERE job_id = %s", (job_id,)).fetchone() is None:
            raise ValueError(f"unknown job: {job_id}")
    redis_client().rpush(
        QUEUE_KEY, json.dumps({"job_id": job_id, "seed": seed}, sort_keys=True)
    )
    return {"job_id": job_id, "seed": seed, "status": "queued"}

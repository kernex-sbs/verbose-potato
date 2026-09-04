"""Postgres and Redis access plus schema bootstrap."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import psycopg
import redis
from psycopg.rows import dict_row

from .config import DATABASE_URL, REDIS_URL


@contextmanager
def connection() -> Iterator[psycopg.Connection[dict[str, Any]]]:
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn


def redis_client() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def initialize(reset: bool = False) -> None:
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with connection() as conn:
        if reset:
            conn.execute("DROP SCHEMA public CASCADE")
            conn.execute("CREATE SCHEMA public")
        conn.execute(schema)
    if reset:
        redis_client().flushdb()


def next_identifier(conn: psycopg.Connection, kind: str) -> tuple[str, int]:
    allowed = {
        "publication": ("publication_id_seq", "pub"),
        "activation": ("activation_id_seq", "act"),
        "job": ("job_id_seq", "job"),
        "completion": ("completion_id_seq", "completion"),
    }
    if kind not in allowed:
        raise ValueError(f"unknown identifier kind: {kind}")
    sequence, prefix = allowed[kind]
    row = conn.execute(f"SELECT nextval('{sequence}') AS value").fetchone()
    assert row is not None
    value = int(row["value"])
    return f"{prefix}-{value}", value


def current_publication(conn: psycopg.Connection, candidate_id: str) -> dict[str, Any] | None:
    return conn.execute(
        """
        SELECT publication_id, publication_seq, candidate_id,
               checkpoint_content_ref, checkpoint_label
        FROM publications
        WHERE candidate_id = %s
        ORDER BY publication_seq DESC
        LIMIT 1
        """,
        (candidate_id,),
    ).fetchone()


def active_contract(conn: psycopg.Connection) -> dict[str, Any] | None:
    return conn.execute(
        """
        SELECT activation_id, activation_seq, contract_content_ref, contract_label
        FROM contract_activations
        ORDER BY activation_seq DESC
        LIMIT 1
        """
    ).fetchone()


def checkpoint_document(conn: psycopg.Connection, ref: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT document FROM checkpoint_contents WHERE checkpoint_content_ref = %s",
        (ref,),
    ).fetchone()
    if row is None:
        raise LookupError(f"unknown checkpoint content: {ref}")
    return row["document"]


def contract_document(conn: psycopg.Connection, ref: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT document FROM contract_contents WHERE contract_content_ref = %s",
        (ref,),
    ).fetchone()
    if row is None:
        raise LookupError(f"unknown contract content: {ref}")
    return row["document"]

"""Small helpers expressing verifier expectations without submitted internals."""

from __future__ import annotations

from typing import Any


def result_for(
    state: dict[str, Any], checkpoint_ref: str, contract_ref: str
) -> dict[str, Any] | None:
    return next(
        (
            row
            for row in state["results"]
            if row["checkpoint_content_ref"] == checkpoint_ref
            and row["contract_content_ref"] == contract_ref
        ),
        None,
    )


def job_for(state: dict[str, Any], job_id: str) -> dict[str, Any]:
    return next(row for row in state["jobs"] if row["job_id"] == job_id)

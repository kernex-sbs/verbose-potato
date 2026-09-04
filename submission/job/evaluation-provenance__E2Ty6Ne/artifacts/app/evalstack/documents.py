"""Load, validate, and identify checkpoint and evaluation-contract documents."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class DocumentError(ValueError):
    pass


def canonical_bytes(document: dict[str, Any]) -> bytes:
    return json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def content_ref(kind: str, document: dict[str, Any]) -> str:
    digest = hashlib.sha256(canonical_bytes(document)).hexdigest()
    return f"{kind}:{digest}"


def load_document(path: str) -> dict[str, Any]:
    candidate = Path(path)
    if not candidate.is_absolute():
        raise DocumentError("document path must be absolute")
    try:
        value = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DocumentError(f"cannot load JSON document: {exc}") from exc
    if not isinstance(value, dict):
        raise DocumentError("document must be a JSON object")
    return value


def validate_checkpoint(document: dict[str, Any]) -> None:
    required = {"format", "run_id", "checkpoint_name", "actions"}
    if set(document) != required:
        raise DocumentError(f"checkpoint fields must be exactly {sorted(required)}")
    if document["format"] != "tabular-policy-v1":
        raise DocumentError("unsupported checkpoint format")
    if not isinstance(document["run_id"], str) or not document["run_id"]:
        raise DocumentError("run_id must be a non-empty string")
    if not isinstance(document["checkpoint_name"], str) or not document["checkpoint_name"]:
        raise DocumentError("checkpoint_name must be a non-empty string")
    actions = document["actions"]
    if not isinstance(actions, dict) or not actions:
        raise DocumentError("actions must be a non-empty object")
    if not all(isinstance(key, str) and isinstance(value, int) for key, value in actions.items()):
        raise DocumentError("actions must map strings to integers")


def validate_contract(document: dict[str, Any]) -> None:
    required = {
        "format",
        "suite_name",
        "dataset_revision",
        "evaluator_revision",
        "aggregation",
        "seeds",
    }
    if set(document) != required:
        raise DocumentError(f"contract fields must be exactly {sorted(required)}")
    if document["format"] != "evaluation-contract-v1":
        raise DocumentError("unsupported contract format")
    for field in ("suite_name", "dataset_revision", "evaluator_revision"):
        if not isinstance(document[field], str) or not document[field]:
            raise DocumentError(f"{field} must be a non-empty string")
    if document["aggregation"] != "sum":
        raise DocumentError("unsupported aggregation")
    seeds = document["seeds"]
    if not isinstance(seeds, list) or not seeds:
        raise DocumentError("seeds must be a non-empty array")
    seen: set[int] = set()
    for seed_entry in seeds:
        if not isinstance(seed_entry, dict) or set(seed_entry) != {"seed", "cases"}:
            raise DocumentError("each seed must contain exactly seed and cases")
        seed = seed_entry["seed"]
        if not isinstance(seed, int) or seed in seen:
            raise DocumentError("seed values must be unique integers")
        seen.add(seed)
        cases = seed_entry["cases"]
        if not isinstance(cases, list):
            raise DocumentError("cases must be an array")
        for case in cases:
            if not isinstance(case, dict) or set(case) != {
                "observation",
                "expected_action",
                "reward",
            }:
                raise DocumentError(
                    "each case must contain observation, expected_action, and reward"
                )
            if not isinstance(case["observation"], str):
                raise DocumentError("observation must be a string")
            if not isinstance(case["expected_action"], int) or not isinstance(
                case["reward"], int
            ):
                raise DocumentError("expected_action and reward must be integers")


def checkpoint_label(document: dict[str, Any]) -> str:
    return f"{document['run_id']}:{document['checkpoint_name']}"


def contract_label(document: dict[str, Any]) -> str:
    return str(document["suite_name"])

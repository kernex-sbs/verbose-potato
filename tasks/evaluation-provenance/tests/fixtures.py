"""Deterministic unseen documents for behavioral provenance traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def checkpoint(variant: int) -> dict[str, Any]:
    actions = {
        1: {"o0": 1, "o1": 0, "o2": 2, "o3": 1, "o4": 0},
        2: {"o0": 0, "o1": 2, "o2": 1, "o3": 0, "o4": 2},
        3: {"o0": 2, "o1": 1, "o2": 0, "o3": 2, "o4": 1},
    }[variant]
    return {
        "format": "tabular-policy-v1",
        "run_id": "hidden-training-run",
        "checkpoint_name": "candidate",
        "actions": actions,
    }


def contract(variant: int, seed_count: int = 2) -> dict[str, Any]:
    base = [
        {
            "seed": 101,
            "cases": [
                {"observation": "o0", "expected_action": variant % 3, "reward": 3},
                {"observation": "o1", "expected_action": (variant + 1) % 3, "reward": 5},
            ],
        },
        {
            "seed": 211,
            "cases": [
                {"observation": "o2", "expected_action": (variant + 2) % 3, "reward": 7},
                {"observation": "o3", "expected_action": variant % 3, "reward": 11},
            ],
        },
        {
            "seed": 307,
            "cases": [
                {"observation": "o4", "expected_action": (variant + 1) % 3, "reward": 13}
            ],
        },
    ]
    return {
        "format": "evaluation-contract-v1",
        "suite_name": "hidden-policy-quality",
        "dataset_revision": f"hidden-dataset-{variant}",
        "evaluator_revision": "policy-match-v1",
        "aggregation": "sum",
        "seeds": base[:seed_count],
    }


def write_json(directory: Path, name: str, value: dict[str, Any]) -> str:
    path = directory / name
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return str(path)

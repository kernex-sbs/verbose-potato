"""Verifier-owned implementation of the scoring contract."""

from __future__ import annotations

from typing import Any


def seed_score(
    checkpoint: dict[str, Any], contract: dict[str, Any], seed: int
) -> int:
    entry = next(item for item in contract["seeds"] if item["seed"] == seed)
    return sum(
        case["reward"]
        for case in entry["cases"]
        if checkpoint["actions"].get(case["observation"])
        == case["expected_action"]
    )


def total_score(checkpoint: dict[str, Any], contract: dict[str, Any]) -> int:
    return sum(seed_score(checkpoint, contract, item["seed"]) for item in contract["seeds"])

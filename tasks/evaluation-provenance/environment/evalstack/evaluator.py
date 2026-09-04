"""Small deterministic policy evaluator used by the runtime."""

from __future__ import annotations

from typing import Any


def seed_score(
    checkpoint: dict[str, Any], contract: dict[str, Any], seed: int
) -> int:
    seed_entry = next(
        (entry for entry in contract["seeds"] if entry["seed"] == seed), None
    )
    if seed_entry is None:
        raise ValueError(f"seed {seed} is not in the evaluation contract")
    actions = checkpoint["actions"]
    return sum(
        case["reward"]
        for case in seed_entry["cases"]
        if actions.get(case["observation"]) == case["expected_action"]
    )

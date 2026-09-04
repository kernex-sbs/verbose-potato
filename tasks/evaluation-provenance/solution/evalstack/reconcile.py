"""Finish accepted legacy deliveries under the repaired snapshot semantics."""

from __future__ import annotations

from .worker import process_one


def main() -> None:
    for _ in range(10_000):
        outcome = process_one()
        if outcome["status"] == "empty":
            return
    raise RuntimeError("pending evaluation queue did not drain")


if __name__ == "__main__":
    main()

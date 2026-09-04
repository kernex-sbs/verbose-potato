"""Create the reproducible, healthy-looking incident shown to the agent."""

from __future__ import annotations

from .db import connection
from .read_model import clear_result_cache
from .scheduler import activate_contract, publish, submit
from .worker import process_one


def seed_incident() -> None:
    with connection() as conn:
        row = conn.execute("SELECT count(*) AS value FROM publications").fetchone()
        assert row is not None
        if int(row["value"]) != 0:
            return

    publish("atlas", "/app/fixtures/checkpoint-a.json")
    activate_contract("/app/fixtures/contract-v1.json")
    submit("atlas")
    while process_one()["status"] != "empty":
        pass

    # A second equivalent request misses the disposable result cache. It is
    # accepted before publication and contract aliases move, then left queued.
    clear_result_cache()
    submit("atlas")

    # The dashboard now presents stale completed work for the new target, and
    # processing the pending delivery would reconstruct inputs from new state.
    publish("atlas", "/app/fixtures/checkpoint-b.json")
    activate_contract("/app/fixtures/contract-v2.json")


if __name__ == "__main__":
    seed_incident()

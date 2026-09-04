# Repair evaluation provenance

The evaluation platform in `/app/evalstack` reports healthy jobs whose scores cannot always be reproduced from the checkpoint content and evaluation contract recorded when the jobs were accepted. Repair the implementation so all of these invariants hold simultaneously:

1. An accepted evaluation snapshots the exact checkpoint content and the complete active evaluation contract. Queueing, seed fanout, retries, and aggregation must keep using that snapshot even if publication or contract state changes later.
2. Completed work is canonical for exactly that checkpoint content and contract content. Identical provenance reuses it without evaluator work; any content difference remains distinct; duplicate delivery cannot duplicate contributions or aggregates.
3. Postgres is durable authority. Losing only Redis's completed-result cache must not lose completed work, change results, or force reevaluation.
4. Checkpoint publications are append-only history. The current leaderboard projects each candidate's current publication under the active contract, independent of evaluation submission or completion order. Republishing old checkpoint content makes the new publication current, may reuse its canonical result, and must not erase history.

Preserve valid existing history and unrelated records. Keep the documented CLI and HTTP contracts unchanged. Their exact JSON schemas, fixture formats, and deterministic scoring rules are in `/app/SPEC.md`. Make all implementation changes under `/app/evalstack`.

Do not use Temporal.io, Trigger.dev, or any other durable-execution or workflow framework.

You have 1800 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.

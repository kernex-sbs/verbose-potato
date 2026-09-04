# Evaluation Provenance

This Harbor task evaluates whether a coding agent can repair durable evaluation provenance without relying on Temporal.io, Trigger.dev, or another workflow framework.

## Durability scope

The agent must make four guarantees hold together:

- evaluations keep the checkpoint and contract snapshot accepted at submission time;
- retries and duplicate deliveries cannot duplicate work or aggregates;
- Postgres remains authoritative when Redis's disposable result cache is lost; and
- checkpoint publications remain append-only while the leaderboard projects current state.

The task focuses on durable provenance and results, not durable Redis queue storage or a general-purpose workflow engine.

## Environment

The editable Python application exposes an `evalctl` CLI and HTTP API. Postgres stores publications, accepted jobs, seed contributions, and canonical results. Redis provides delivery and result caching. The verifier runs separately with fresh Postgres and Redis services, then replays the database snapshot collected from the agent environment.

Agent networking follows the benchmark default; the verifier network is internal. No external service is required.

## Layout

```text
evaluation-provenance/
├── instruction.md       # prompt shown to the agent
├── task.toml           # Harbor metadata and resource limits
├── environment/        # intentionally faulty application and services
├── solution/           # reference repair used by the oracle
└── tests/              # separate behavioral verifier
```

## Verification

From the repository root:

```bash
scripts/qa.sh tasks/evaluation-provenance
harbor run -p tasks/evaluation-provenance -a oracle
harbor run -p tasks/evaluation-provenance -a nop
```

Expected rewards are `1.0` for the oracle and `0.0` for the no-op agent.

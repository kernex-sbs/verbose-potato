# Evaluation Provenance

A Harbor task for evaluating whether an AI coding agent can repair durable state and provenance in a production-style ML evaluation service.

The task uses Python, Postgres, and Redis. It deliberately does not use Temporal.io, Trigger.dev, or another durable-execution framework; the agent must implement the required guarantees directly in the existing application.

## What the task evaluates

The agent inherits a healthy-looking service with subtle provenance failures and must make four properties hold together:

- **Acceptance-time snapshots:** queued work keeps the exact checkpoint and evaluation contract accepted at submission time.
- **Idempotent computation:** retries and duplicate deliveries cannot duplicate seed contributions or canonical results.
- **Durable authority:** Postgres remains authoritative when Redis's disposable result cache is lost.
- **Append-only history:** publications remain auditable while the leaderboard reflects the current publication and active contract.

This scopes durability to reproducible evaluation state and results. It does not attempt to build a general-purpose workflow engine or make the Redis queue itself durable.

## Architecture

```text
Harbor agent
    └── editable Python service
        ├── Postgres   durable provenance and canonical results
        └── Redis      delivery queue and disposable result cache

Harbor verifier
    ├── patched source collected from the agent container
    ├── data-only snapshot collected from agent-side Postgres
    └── fresh Postgres and Redis on an isolated verifier network
```

The verifier exercises only the documented CLI and HTTP interfaces. Expected scores are derived independently from hidden fixture contents.

## Repository layout

```text
.
├── tasks/evaluation-provenance/
│   ├── instruction.md       agent prompt
│   ├── task.toml           Harbor configuration
│   ├── environment/        intentionally faulty application
│   ├── solution/           oracle reference repair
│   └── tests/              separate behavioral verifier
├── submission/
│   ├── REPORT.md            design and rollout analysis
│   ├── grading/             generated scorecard and rubric review
│   └── job/                 submitted five-trial Harbor job
└── scripts/                     QA, grading, and submission helpers
```

See [the task README](tasks/evaluation-provenance/README.md) for the task-specific layout and [the submission report](submission/REPORT.md) for verifier coverage and failure analysis.

## Prerequisites

- Docker with Compose support
- [Harbor](https://github.com/harbor-framework/harbor) `0.14.0`
- An OpenRouter API key only when running model rollouts

```bash
uv tool install harbor==0.14.0
harbor --version
docker ps
```

For model rollouts, copy `.env.example` to `.env` and add the provided key. `.env` is ignored by Git.

## Verify the task

Run the static checks:

```bash
scripts/qa.sh tasks/evaluation-provenance
```

Confirm that the reference solution passes and a no-op fails:

```bash
harbor run -p tasks/evaluation-provenance -a oracle
harbor run -p tasks/evaluation-provenance -a nop
```

Expected rewards are `1.0` for the oracle and `0.0` for the no-op agent.

## Run an agent evaluation

```bash
harbor run --env-file .env \
  -p tasks/evaluation-provenance \
  -a claude-code \
  -m anthropic/claude-sonnet-5 \
  --n-attempts 5
```

Then grade and package the completed job:

```bash
python3 scripts/grade.py jobs/<job-name>
python3 scripts/submit.py jobs/<job-name>
```

## Recorded result

The submitted five-rollout evaluation produced:

- agent pass rate: **2/5 (40%)**;
- oracle reward: **1.0**;
- no-op reward: **0.0**; and
- implementation rubric failures: **0/30**.

One agent missed the Postgres fallback required after Redis cache loss. Two others erased inherited durable history during final cleanup. The remaining two agents satisfied all verifier scenarios. Full evidence is in [submission/REPORT.md](submission/REPORT.md).

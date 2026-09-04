# Evaluation platform contract

`/app/evalstack` is the only editable implementation. Commands emit exactly one JSON object on stdout and diagnostics on stderr. A nonzero exit means the operation failed.

## Content formats and score

A checkpoint JSON object has this schema:

```text
{
  "format": "tabular-policy-v1",
  "run_id": string,
  "checkpoint_name": string,
  "actions": { observation: integer, ... }
}
```

An evaluation-contract JSON object has this schema:

```text
{
  "format": "evaluation-contract-v1",
  "suite_name": string,
  "dataset_revision": string,
  "evaluator_revision": string,
  "aggregation": "sum",
  "seeds": [
    {
      "seed": integer,
      "cases": [
        {"observation": string, "expected_action": integer, "reward": integer},
        ...
      ]
    },
    ...
  ]
}
```

Seed score is the sum of `reward` for cases where the checkpoint action for `observation` equals `expected_action`; missing observations do not match. Canonical score is the sum of all seed scores. Seed integers are unique within a contract. Every field and nested value in either JSON document is part of its content identity, including labels such as `run_id`, `checkpoint_name`, and `suite_name`. Identity reference strings are opaque to callers.

## CLI

Run commands as `evalctl <operation>` or `python -m evalstack.cli <operation>`.

- `init [--reset]` creates the schema and returns `{"ok": boolean}`. `--reset` is an administrative test helper that clears application state.
- `publish --candidate ID --checkpoint ABSOLUTE_JSON_PATH` appends a publication and returns `{"candidate_id": string, "publication_id": string, "checkpoint_content_ref": string}`.
- `activate-contract --contract ABSOLUTE_JSON_PATH` appends a contract activation and returns `{"activation_id": string, "contract_content_ref": string}`.
- `submit --candidate ID` accepts the candidate's current publication under the active contract. It returns `{"job_id": string, "candidate_id": string, "publication_id": string, "checkpoint_content_ref": string, "contract_content_ref": string, "status": "queued"|"complete", "reused": boolean}`. Missing current state is an error.
- `process-one` handles at most one queued seed delivery and returns `{"status": "empty"}` or `{"status": "processed"|"duplicate"|"complete", "job_id": string, "seed": integer|null, "checkpoint_content_ref": string, "contract_content_ref": string, "score": integer|null}`. It may enqueue remaining seed work.
- `retry-one --job ID --seed INTEGER` enqueues a delivery for an existing accepted job and returns `{"job_id": string, "seed": integer, "status": "queued"}`.
- `clear-result-cache` deletes only disposable completed-result cache entries and returns `{"deleted": integer}`. It must not delete pending queue deliveries.
- `leaderboard` returns the same object as `GET /v1/leaderboard`.
- `inspect [--candidate ID]` returns `{"publications": array, "activations": array, "jobs": array, "seed_results": array, "results": array}`. The row schemas are:
  - publication: `{"publication_id": string, "publication_seq": integer, "candidate_id": string, "checkpoint_content_ref": string, "checkpoint_label": string}`;
  - activation: `{"activation_id": string, "activation_seq": integer, "contract_content_ref": string, "contract_label": string}`;
  - job: `{"job_id": string, "job_seq": integer, "candidate_id": string, "publication_id": string, "checkpoint_content_ref": string, "contract_content_ref": string, "checkpoint_label": string, "contract_label": string, "status": "queued"|"running"|"complete", "reused": boolean, "resolved_checkpoint_content_ref": string|null, "resolved_contract_content_ref": string|null, "completed_seq": integer|null}`;
  - seed result: `{"checkpoint_content_ref": string, "contract_content_ref": string, "seed": integer, "score": integer, "source_job_id": string}`;
  - canonical result: `{"checkpoint_content_ref": string, "contract_content_ref": string, "score": integer, "seed_count": integer, "completed_by_job_id": string, "completed_seq": integer}`.
  Extra diagnostic fields are allowed on rows. With `--candidate`, only publications and jobs are filtered; activations and canonical computation history remain global.
- `metrics` returns `{"evaluator_invocations": integer, "publication_count": integer, "job_count": integer, "seed_result_count": integer, "result_count": integer}`.

Publication and activation identifiers are opaque, unique, and monotonically ordered by their creation events. Queue processing order is FIFO. `process-one` is deterministic and never waits for future work.

## HTTP

`python -m evalstack.api` serves:

- `GET /health` -> `200 {"status":"ok"}`.
- `POST /v1/evaluations` with `{"candidate_id": string}` -> `202` and exactly the `submit` response schema; missing/invalid state -> `409 {"error": string}`.
- `GET /v1/leaderboard` -> `200` with:

```text
{
  "contract_content_ref": string|null,
  "entries": [
    {
      "candidate_id": string,
      "publication_id": string,
      "checkpoint_content_ref": string,
      "contract_content_ref": string|null,
      "status": "pending"|"complete",
      "score": integer|null
    },
    ... sorted by candidate_id
  ]
}
```

When there is no active contract, `contract_content_ref` is null and every published candidate is pending. A historical result that does not match both the current publication's checkpoint content and the active contract must never be displayed as current.

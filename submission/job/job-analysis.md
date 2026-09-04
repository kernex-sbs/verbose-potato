## Job Summary: evaluation-provenance (5 trials)

**Overall: 2 pass (reward 1.0), 3 fail (reward 0.0).** All same task family, same agent (Claude Sonnet 5).

- Pass: `jUnvQvZ`, `eR9PsAy` — full fix, all 5 hidden tests, clean.
- Fail: `E2Ty6Ne`, `GMpQT58`, `5hm9BB4` — reward 0.0 each, but for different reasons.

### Common failure pattern — self-inflicted, not conceptual (2 of 3 fails)

`E2Ty6Ne` and `GMpQT58` both correctly diagnosed and fixed all provenance bugs (verified manually via CLI/HTTP), then **destroyed own work** by running `evalctl init --reset` as a "cleanup" step, wiping seeded history the task explicitly said to preserve. Verifier's pg_dump caught empty DB → every hidden test errored at fixture setup (`assert len(atlas_publications) >= 2` → got 0). Reward 0 despite correct logic. This is an execution-discipline bug (destructive command hygiene), not a provenance-reasoning failure — flagged in `difficulty_crux` for both.

`5hm9BB4` failed differently: agent fixed 3 of 4 bugs (cache key content-addressing, worker snapshot use, leaderboard join) but left `scheduler.submit()` checking Redis cache for reuse instead of Postgres `canonical_results` directly — violates invariant 3 (Postgres durable authority). 4/5 tests passed; failed only `test_identity_algebra_reuse_separation_and_cache_loss`. Genuine near-miss on real logic.

### Per-criterion aggregate

- **task_specification**: 5/5 pass. SPEC.md + instruction.md consistently sufficient; no trial failed from missing/ambiguous spec.
- **reward_hacking**: 5/5 pass. No test/reward-file tampering, no solution/ access, anywhere. All edits confined to `/app/evalstack`.
- **difficulty_crux**: 3/5 pass, 2/5 fail (`E2Ty6Ne`, `GMpQT58`). Both fails are the same shape: agent solved intended identity/provenance puzzle correctly but tripped an unrelated operational trap (`--reset` wiping history) that isn't what the task is designed to probe. Worth rewording task to warn against destructive `init --reset` during verification, or making it non-destructive/blocked.
- **near_miss**: 4/5 pass, 1/5 fail (`5hm9BB4`). Flag: this trial is a genuine near-miss (4/5 tests, one missed call-site), not a calibration artifact — the reset-wipe fails (`E2Ty6Ne`/`GMpQT58`) are NOT near-misses despite correct logic, since verifier fails wholesale/structurally (0 vs required rows) before any invariant logic runs.
- **refusals**: 5/5 pass. No refusal language in any trial; no sensitive-topic trigger.
- **low_timeout**: 5/5 pass. All trials finished well under 1800s budget (344s–468s range for passes, 320–470s for fails) — no time pressure involved in any failure.

### Takeaway

Agent reliably solves core provenance-identity challenge (content-addressed refs, snapshot-at-accept, canonical reuse, leaderboard projection) — 2 clean passes, 1 near-complete (`5hm9BB4`). Biggest risk isn't reasoning, it's **destructive verification hygiene**: 2 of 3 fails come from agent running `init --reset` as a final step and nuking required seeded history. Consider: (a) reword instructions to explicitly warn against `--reset` post-seed, or (b) make `--reset` unavailable/gated after seeding in the harness.

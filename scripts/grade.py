#!/usr/bin/env python3
"""Evaluate an existing Harbor job using the repository's included checks.

Evaluation only (use scripts/submit.py to package). It does not re-run the agent,
so it never spends rollout budget — but the rubric review and trial analysis are
LLM judge calls, so each run costs a little judge credit on the same key.

    python3 grade.py <job-dir> [task-dir] [--model M]

    <job-dir>    A Harbor job to grade, e.g. jobs/<job-name> (with N trials).
    [task-dir]   Default: autodetected if exactly one dir under tasks/.
    --model      Judge model for review/analyze. Default: anthropic/claude-sonnet-5

The key is read from the environment, with ./.env filling unset vars. Writes under
<job-dir>/grading/: grade.json (scorecard), rubric-review.json (harbor check).
(harbor check). harbor analyze writes its own job-analysis.json + per-trial files
into the job dir; submit.py renames those so a name never maps to two schemas.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repo root (this script lives in scripts/)


def fail(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def compute_pass_rate(job_dir: Path) -> tuple[int, int, int | None]:
    """(passed, total, rate%) from the job's verifier/reward.txt files."""
    rewards = [rf for rf in job_dir.rglob("reward.txt") if rf.parent.name == "verifier"]
    total = len(rewards)
    passed = sum(1 for rf in rewards if rf.read_text().strip() in ("1", "1.0"))
    rate = round(passed / total * 100) if total else None
    return passed, total, rate


def resolve_run_env() -> dict[str, str]:
    """Environment for Harbor's LLM graders: the real environment, with ./.env
    filling in any unset vars (the load_dotenv pattern), then OpenRouter creds
    normalized for the judge (harbor check/analyze read ANTHROPIC_API_KEY).
    """
    parsed: dict[str, str] = {}
    dotenv = ROOT / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            val = re.sub(
                r"\$\{(\w+)\}",
                lambda m: parsed.get(m.group(1), os.environ.get(m.group(1), "")),
                val,
            )
            parsed[key] = val

    env = {**parsed, **os.environ}  # already-exported vars win over .env
    if env.get("OPENROUTER_API_KEY"):
        env.setdefault("ANTHROPIC_AUTH_TOKEN", env["OPENROUTER_API_KEY"])
        env.setdefault("ANTHROPIC_BASE_URL", "https://openrouter.ai/api")
    if not env.get("ANTHROPIC_API_KEY") and env.get("ANTHROPIC_AUTH_TOKEN"):
        env["ANTHROPIC_API_KEY"] = env["ANTHROPIC_AUTH_TOKEN"]
    return env


def require_harbor():
    if shutil.which("harbor") is None:
        fail("harbor CLI required (uv tool install harbor==0.14.0)")


def reward_of_job(job_dir: Path) -> str:
    for rf in job_dir.rglob("reward.txt"):
        if rf.parent.name == "verifier":
            return rf.read_text().strip()
    return "missing"


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True, description="Grade a Harbor job.")
    ap.add_argument("job_dir")
    ap.add_argument("task_dir", nargs="?")
    ap.add_argument("--model", default="anthropic/claude-sonnet-5")
    args = ap.parse_args()

    job_dir = Path(args.job_dir).resolve()
    if not job_dir.is_dir():
        fail(f"job directory not found: {job_dir}")

    if args.task_dir:
        task_dir = Path(args.task_dir).resolve()
    else:
        tasks = [d for d in (ROOT / "tasks").glob("*") if d.is_dir()]
        if len(tasks) != 1:
            fail("could not autodetect a single task under tasks/; pass the task dir", 2)
        task_dir = tasks[0].resolve()
    if not task_dir.is_dir():
        fail(f"task directory not found: {task_dir}")

    out_dir = job_dir / "grading"
    out_dir.mkdir(exist_ok=True)

    lines: list[str] = []
    overall = 0  # hard problem (❌)
    warn = 0     # soft warning (⚠️)

    def record(emoji: str, msg: str):
        nonlocal warn
        lines.append(f"{emoji} {msg}")
        if emoji == "⚠️":
            warn = 1
        print(f"{emoji} {msg}")

    print(f"Grading job:  {job_dir}")
    print(f"Against task: {task_dir}\n")

    # 1. pass rate from the job's committed rewards (no key)
    passed, total, rate = compute_pass_rate(job_dir)
    if rate is None:  # rate is None iff total == 0; narrows rate to int below
        record("❌", f"no trials with a reward found under {job_dir}")
        overall = 1
    else:
        if rate <= 20:
            band = "BEST (≤20%)"
        elif rate <= 40:
            band = "great (≤40%)"
        elif rate <= 60:
            band = "good (≤60%)"
        else:
            band = "outside target (>60%)"
        if rate <= 60:
            record("✅", f"pass rate: {passed}/{total} = {rate}% — {band}")
        else:
            record("⚠️", f"pass rate: {passed}/{total} = {rate}% — {band} (too easy)")

    # 2. oracle / nop verifier sanity (no key)
    require_harbor()
    tmp = out_dir / "_exec"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    results = {}
    for agent in ("oracle", "nop"):
        r = subprocess.run(
            ["harbor", "run", "--jobs-dir", str(tmp), "--job-name", agent,
             "-p", str(task_dir), "-a", agent],
            capture_output=True, text=True)
        results[agent] = reward_of_job(tmp / agent) if r.returncode == 0 else "error"
    o, n = results["oracle"], results["nop"]
    if o in ("1", "1.0") and n not in ("1", "1.0"):
        record("✅", f"oracle={o} nop={n} (verifier accepts solution, rejects no-op)")
    else:
        record("❌", f"oracle={o} nop={n} (expected oracle=1.0, nop<1.0)")
        overall = 1
    shutil.rmtree(tmp, ignore_errors=True)  # keep temp jobs out of committed grading/

    # 3. LLM graders: rubric review + trial analysis (needs key from env / .env)
    rubric_failed: int | None = None
    rubric_total: int | None = None
    run_env = resolve_run_env()
    if not (run_env.get("ANTHROPIC_API_KEY") or run_env.get("ANTHROPIC_AUTH_TOKEN")):
        record("❌", "no API key found (set OPENROUTER_API_KEY in .env, or export it)")
        overall = 1
    else:
        review_json = out_dir / "rubric-review.json"
        r = subprocess.run(
            ["harbor", "check", str(task_dir),
             "-r", str(ROOT / "rubrics/task-implementation.toml"),
             "-m", args.model, "-o", str(review_json)],
            capture_output=True, text=True, env=run_env)
        if r.returncode == 0 and review_json.is_file():
            try:
                data = json.loads(review_json.read_text())
                checks = data.get("checks", data)
                vals = list(checks.values() if isinstance(checks, dict) else checks)
                rubric_total = len(vals)
                rubric_failed = sum(1 for v in vals
                                    if str((v or {}).get("outcome", "")).lower()
                                    in ("fail", "failed", "false"))
            except (json.JSONDecodeError, TypeError, AttributeError, KeyError):
                rubric_failed = rubric_total = None
            if rubric_failed is None:
                record("⚠️", f"rubric review: could not parse result → {review_json}")
            elif rubric_failed == 0:
                record("✅", f"rubric review: no failed criteria → {review_json}")
            else:
                record("⚠️", f"rubric review: {rubric_failed} failed criterion(s) → {review_json}")
        else:
            record("❌", "rubric review (harbor check) failed to run")
            overall = 1

        # No -o: harbor analyze writes analysis.json into the job dir natively;
        # -o would just duplicate it under grading/.
        r = subprocess.run(
            ["harbor", "analyze", str(job_dir),
             "-r", str(ROOT / "rubrics/trial-analysis.toml"),
             "--job-prompt", str(ROOT / "rubrics/trial-analysis-job.txt"),
             "-m", args.model],
            capture_output=True, text=True, env=run_env)
        if r.returncode == 0:
            record("✅", "trial analysis generated (job + per-trial, in the job dir)")
        else:
            record("⚠️", "trial analysis (harbor analyze) did not complete")

    # scorecard: grade.json is the single source of truth. No grade.md — the
    # human view is the rendered PR comment (and grade.py's own stdout above).
    band_key = (None if rate is None
                else "best" if rate <= 20
                else "great" if rate <= 40
                else "good" if rate <= 60
                else "outside")
    grade = {
        "job": job_dir.name,
        "task": task_dir.name,
        "pass_rate": {"passed": passed, "total": total, "pct": rate, "band": band_key},
        "oracle": o,
        "nop": n,
        "rubric": {"failed": rubric_failed, "total": rubric_total},
    }
    (out_dir / "grade.json").write_text(json.dumps(grade, indent=2) + "\n")

    print(f"\nWrote {out_dir}/{{grade.json,rubric-review.json}}")
    if overall:
        print("NOT READY ❌ — fix the ❌ items above and re-grade.")
    elif warn:
        print("READY, WITH WARNINGS ⚠️ — review the ⚠️ items (e.g. pass rate outside target) before submitting.")
    else:
        print("READY ✅ — now package it: python3 scripts/submit.py <job-dir>")
    return overall


if __name__ == "__main__":
    sys.exit(main())

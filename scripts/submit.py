#!/usr/bin/env python3
"""Package an already-graded rollout into submission/ — packaging only.

submit.py does not run or grade rollouts. Grade the job first (scripts/grade.py);
submit.py then copies that graded job into submission/job/, refusing if it has no
grading/grade.json. It leaves submission/REPORT.md (the template) for you to fill.

jobs/ is gitignored local scratch; submission/job/ is the single committed copy of
the chosen rollout (grade.json records which jobs/ run it came from). The scorecard
is promoted to submission/grading/ (sibling of job/), not nested inside it.

    harbor run …               produce rollouts   (jobs/<job>/)
    python3 scripts/grade.py <job>   evaluate     (jobs/<job>/grading/)
    python3 scripts/submit.py <job>  package      (submission/)

Usage: python3 scripts/submit.py <job-dir>
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent


def fail(msg: str, code: int = 1) -> int:
    print(msg, file=sys.stderr)
    return code


def rename_analysis(job_out: Path) -> None:
    """Rename Harbor's analysis.json so one name = one schema: job root →
    job-analysis.{json,md}, per-trial (dirs with a verifier/) → trial-analysis.*"""
    for ext in ("json", "md"):
        root_file = job_out / f"analysis.{ext}"
        if root_file.is_file():
            root_file.rename(job_out / f"job-analysis.{ext}")
    for trial in job_out.iterdir():
        if not trial.is_dir() or not (trial / "verifier").is_dir():
            continue
        for ext in ("json", "md"):
            trial_file = trial / f"analysis.{ext}"
            if trial_file.is_file():
                trial_file.rename(trial / f"trial-analysis.{ext}")


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args[:1] in (["-h"], ["--help"]) else 2

    job_dir = Path(args[0]).resolve()
    if not job_dir.is_dir():
        return fail(f"job directory not found: {job_dir}")

    # require the job to already be graded — submit.py packages, it does not grade
    grade_json = job_dir / "grading" / "grade.json"
    if not grade_json.is_file():
        return fail(
            f"job is not graded: {grade_json} not found.\n"
            f"Grade it first:  python3 scripts/grade.py {job_dir.name}")

    # assemble submission/: refresh the rollout copy, keep your REPORT.md
    sub = ROOT / "submission"
    sub.mkdir(exist_ok=True)
    job_out = sub / "job"
    if job_out.exists():
        shutil.rmtree(job_out)
    shutil.copytree(job_dir, job_out)
    rename_analysis(job_out)

    # promote the scorecard to submission/grading/ (sibling of job/) so the
    # top level reads as: REPORT.md (writeup) / grading/ (verdict) / job/ (evidence)
    grading_out = sub / "grading"
    if grading_out.exists():
        shutil.rmtree(grading_out)
    shutil.move(str(job_out / "grading"), str(grading_out))

    if not (sub / "REPORT.md").is_file():
        print("⚠️  submission/REPORT.md is missing — restore it from the repo and "
              "fill it in before submitting.")

    rate = (json.loads(grade_json.read_text()).get("pass_rate") or {}).get("pct")
    rate_str = "n/a" if rate is None else f"{rate}%"
    print(f"\n== packaged submission/ from {job_dir.name} (pass rate {rate_str}) ==")
    print("Fill in submission/REPORT.md, commit submission/ (and your task), open a PR.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Render a PR comment (markdown, to stdout) from a grading directory.

Deterministic formatting only — no model calls, no secrets. Reads grade.json
(scorecard), rubric-review.json, and ../job-analysis.json and lays them out; does
no parsing of human markdown. CI-only helper for the Grading Summary workflow.

    python3 .github/scripts/render-grading-comment.py [grading-dir]
    # default grading-dir: submission/grading
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

OUTCOME_EMOJI = {"pass": "✅", "fail": "❌", "not_applicable": "⚪"}
BAND_TEXT = {
    "best": "**BEST** (≤20%)",
    "great": "great (≤40%)",
    "good": "good (≤60%)",
    "outside": "⚠️ outside target (>60%, too easy)",
}


def is_failed(outcome: object) -> bool:
    return str(outcome).lower() in ("fail", "failed", "false")


def load_json(path: Path) -> dict:
    if path.is_file():
        try:
            data = json.loads(path.read_text())
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def derive_models(job_dir: Path) -> list[str]:
    """Best-effort model id(s) the job was evaluated on, e.g. ['claude-sonnet-5'].

    A pass rate only means something next to the model it was measured against —
    0% on Sonnet 5 is a different result from 0% on another model. Prefer
    result.json eval keys ({agent}__{model}__{suffix}); fall back to config.json
    agents[].model_name (dropping any provider/ prefix). De-duped, order-preserving.
    """
    models: list[str] = []
    evals = (load_json(job_dir / "result.json").get("stats") or {}).get("evals") or {}
    if isinstance(evals, dict):
        for key in evals:
            parts = str(key).split("__")
            if len(parts) >= 2 and parts[1]:
                models.append(parts[1])
    if not models:
        for agent in load_json(job_dir / "config.json").get("agents") or []:
            name = str((agent or {}).get("model_name") or "").strip()
            if name:
                models.append(name.split("/")[-1])  # drop provider prefix
    seen: set[str] = set()
    return [m for m in models if not (m in seen or seen.add(m))]


def main() -> int:
    grading = Path(sys.argv[1] if len(sys.argv) > 1 else "submission/grading")
    grade = load_json(grading / "grade.json")
    review = load_json(grading / "rubric-review.json")
    # grading/ is a sibling of job/; the rollout (analysis + config) lives in job/
    job = grading.parent / "job"
    analysis = load_json(job / "job-analysis.json")

    # headline — task, pass rate, band, model(s)
    task = str(grade.get("task") or "your task")
    models = derive_models(job)
    model_inline = (" on " + ", ".join(f"`{m}`" for m in models)) if models else ""
    pr = grade.get("pass_rate") or {}
    pct = pr.get("pct")
    if isinstance(pct, int):
        band = BAND_TEXT.get(pr.get("band"), f"{pct}%")
        headline = (f"**Pass rate: {pct}% ({pr.get('passed')}/{pr.get('total')})"
                    f"{model_inline}** — {band}")
    else:
        headline = "_pass rate unavailable_" + (
            f" — model: {', '.join(models)}" if models else "")

    # oracle / nop — from grade.json fields
    oracle, nop = grade.get("oracle"), grade.get("nop")
    if oracle is not None and nop is not None:
        ok = str(oracle).startswith("1")
        oracle_txt = ("✅ " if ok else "❌ ") + f"oracle={oracle} nop={nop}"
    else:
        oracle_txt = "—"

    # rubric review tally (rubric-review.json)
    checks = review.get("checks", review) if isinstance(review, dict) else {}
    rfail = {k: v for k, v in checks.items() if isinstance(v, dict) and is_failed(v.get("outcome"))}
    rubric_txt = (f"⚠️ {len(rfail)} / {len(checks)} criteria failed" if rfail
                  else f"✅ {len(checks)} / {len(checks)} passed" if checks else "—")

    # trial-analysis tally (job-analysis.json: trials[].checks[crit].outcome)
    trials = analysis.get("trials", []) if isinstance(analysis, dict) else []
    tally: dict[str, dict[str, int]] = {}
    for t in trials:
        for crit, v in (t.get("checks") or {}).items():
            outcome = str(v.get("outcome") if isinstance(v, dict) else v)
            tally.setdefault(crit, {})[outcome] = tally.setdefault(crit, {}).get(outcome, 0) + 1

    out: list[str] = []
    out.append(f"## 📊 Grading summary — `{task}`")
    out.append("")
    out.append(headline)
    out.append("")
    out.append("| Check | Result |\n|---|---|")
    out.append(f"| Oracle / nop | {oracle_txt} |")
    out.append(f"| Rubric review | {rubric_txt} |")
    out.append(f"| Trial analysis | {'✅ generated' if trials else '—'} |")

    if rfail:
        out.append(f"\n<details><summary>❌ {len(rfail)} failed rubric criteria</summary>\n")
        for k, v in rfail.items():
            out.append(f"- **{k}** — {str(v.get('explanation', '')).strip()}")
        out.append("\n</details>")

    if tally:
        line = " · ".join(
            f"**{crit}**: " + " ".join(f"{n}{OUTCOME_EMOJI.get(o, '•')}" for o, n in sorted(counts.items()))
            for crit, counts in tally.items()
        )
        out.append(f"\n<details><summary>🔬 Trial analysis ({len(trials)} trials)</summary>\n")
        out.append(line)
        job_summary = analysis.get("job_summary")
        if isinstance(job_summary, str) and job_summary.strip():
            out.append("\n" + job_summary.strip())
        out.append("\n</details>")

    out.append("\n<sub>Rendered from <code>submission/grading/</code>. Updates on each push.</sub>")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

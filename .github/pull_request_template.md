## Checklist

Once the following criteria are met, please mark the PR `READY_FOR_REVIEW`. Submissions may not be reviewed if they don't meet the following requirements.

- [ ] The `instruction.md` and `REPORT.md` was written by a human.
- [ ] The final 5-rollout job was run with the required model, graded (`python3 scripts/grade.py jobs/<final-job-name>`), and packaged into `submission/` (`python3 scripts/submit.py jobs/<final-job-name>`).
- [ ] Grading passes: oracle scores 1.0, no-op scores 0.0, and the rubric review has no failed criteria.
- [ ] `submission/REPORT.md` explains the task, results, and why failures reflect task difficulty rather than task bugs — and the trial analysis supports its claims.
- [ ] The `Grading summary` GitHub Actions comment renders with the full `Job Summary` under the `Trial analysis` dropdown.

## REPORT.md

<!-- Paste the contents of submission/REPORT.md below. -->

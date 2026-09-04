#!/usr/bin/env bash
# Static checks — runs the ci_checks/*.sh suite, the same set CI runs on every PR.
# No API key, no Docker, no rollouts; just lints your task's files.
#
# Usage:
#   scripts/qa.sh [task-dir]   # task-dir autodetected if exactly one under tasks/

set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TASK="${1:-}"
if [[ -z "$TASK" ]]; then
  tasks=()
  for d in "$ROOT"/tasks/*/; do [[ -d "$d" ]] && tasks+=("$d"); done
  if [[ "${#tasks[@]}" -eq 1 ]]; then
    TASK="${tasks[0]}"
  else
    echo "could not autodetect a single task under tasks/; pass the task dir" >&2
    exit 2
  fi
fi
[[ -d "$TASK" ]] || { echo "task directory not found: $TASK" >&2; exit 1; }

fail=0
for check in "$ROOT"/ci_checks/check-*.sh; do
  [[ -e "$check" ]] || continue
  if bash "$check" "$TASK" >/dev/null 2>&1; then
    echo "✅ $(basename "$check")"
  else
    echo "❌ $(basename "$check")"
    bash "$check" "$TASK" 2>&1 | sed 's/^/     /'
    fail=1
  fi
done

echo
if [[ "$fail" -eq 0 ]]; then echo "All static checks pass."; else echo "Some static checks failed."; fi
exit "$fail"

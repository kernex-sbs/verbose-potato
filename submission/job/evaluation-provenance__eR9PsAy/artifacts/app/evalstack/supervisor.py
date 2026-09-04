"""Keep the development API running and reload it after source edits."""

from __future__ import annotations

import signal
import subprocess
import sys
import time
from pathlib import Path


SOURCE_DIR = Path(__file__).resolve().parent


def source_snapshot() -> tuple[tuple[str, int], ...]:
    return tuple(
        (path.name, path.stat().st_mtime_ns)
        for path in sorted(SOURCE_DIR.glob("*.py"))
    )


def main() -> int:
    stopping = False
    child: subprocess.Popen[bytes] | None = None

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True
        if child is not None and child.poll() is None:
            child.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    while not stopping:
        baseline = source_snapshot()
        child = subprocess.Popen([sys.executable, "-m", "evalstack.api"])
        while not stopping and child.poll() is None:
            time.sleep(0.2)
            if source_snapshot() != baseline:
                child.terminate()
                break
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
        if not stopping:
            time.sleep(0.2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

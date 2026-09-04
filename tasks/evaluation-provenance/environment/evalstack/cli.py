"""JSON command-line interface for deterministic platform operations."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable

from .db import initialize
from .read_model import clear_result_cache, inspect, leaderboard, metrics
from .scheduler import activate_contract, publish, retry_one, submit
from .worker import process_one


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="evalctl")
    commands = root.add_subparsers(dest="command", required=True)

    init_command = commands.add_parser("init")
    init_command.add_argument("--reset", action="store_true")

    publish_command = commands.add_parser("publish")
    publish_command.add_argument("--candidate", required=True)
    publish_command.add_argument("--checkpoint", required=True)

    contract_command = commands.add_parser("activate-contract")
    contract_command.add_argument("--contract", required=True)

    submit_command = commands.add_parser("submit")
    submit_command.add_argument("--candidate", required=True)

    commands.add_parser("process-one")

    retry_command = commands.add_parser("retry-one")
    retry_command.add_argument("--job", required=True)
    retry_command.add_argument("--seed", required=True, type=int)

    commands.add_parser("clear-result-cache")
    commands.add_parser("leaderboard")

    inspect_command = commands.add_parser("inspect")
    inspect_command.add_argument("--candidate")

    commands.add_parser("metrics")
    return root


def execute(arguments: argparse.Namespace) -> dict[str, Any]:
    command = arguments.command
    if command == "init":
        initialize(reset=arguments.reset)
        return {"ok": True}
    if command == "publish":
        return publish(arguments.candidate, arguments.checkpoint)
    if command == "activate-contract":
        return activate_contract(arguments.contract)
    if command == "submit":
        return submit(arguments.candidate)
    if command == "process-one":
        return process_one()
    if command == "retry-one":
        return retry_one(arguments.job, arguments.seed)
    if command == "clear-result-cache":
        return clear_result_cache()
    if command == "leaderboard":
        return leaderboard()
    if command == "inspect":
        return inspect(arguments.candidate)
    if command == "metrics":
        return metrics()
    raise AssertionError(f"unhandled command: {command}")


def main() -> int:
    try:
        result = execute(parser().parse_args())
    except Exception as exc:  # CLI boundary: one diagnostic, nonzero status.
        print(f"evalctl: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

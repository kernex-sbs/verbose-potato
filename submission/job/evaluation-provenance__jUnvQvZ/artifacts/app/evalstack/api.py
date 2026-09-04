"""Minimal JSON HTTP boundary around the platform service."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .config import HTTP_HOST, HTTP_PORT
from .read_model import leaderboard
from .scheduler import submit


class Handler(BaseHTTPRequestHandler):
    server_version = "evalstack/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path == "/health":
            self._send(200, {"status": "ok"})
            return
        if self.path == "/v1/leaderboard":
            try:
                self._send(200, leaderboard())
            except Exception as exc:
                self._send(500, {"error": str(exc)})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path != "/v1/evaluations":
            self._send(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            value = json.loads(self.rfile.read(length))
            if not isinstance(value, dict) or set(value) != {"candidate_id"}:
                raise ValueError("body must contain exactly candidate_id")
            if not isinstance(value["candidate_id"], str) or not value["candidate_id"]:
                raise ValueError("candidate_id must be a non-empty string")
            self._send(202, submit(value["candidate_id"]))
        except Exception as exc:
            self._send(409, {"error": str(exc)})


def main() -> None:
    ThreadingHTTPServer((HTTP_HOST, HTTP_PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()

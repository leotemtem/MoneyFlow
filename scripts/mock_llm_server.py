#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Minimal OpenAI-compatible mock server for harness validation (stdlib only).

Serves just enough of the Chat Completions API to exercise MoneyFlow's
OpenAI-compatible AI provider end-to-end without any real or paid model. It is
intended only for automated Docker/harness validation — never for production.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "0.0.0.0"  # noqa: S104 - test-only container, bound inside a private network
PORT = 8000

# Deterministic marker so the harness AI smoke test can assert on the response.
CANNED_CONTENT = (
    "MOCK INSIGHT: Your finances look balanced. Top category is Groceries; "
    "consider setting a small monthly savings target."
)


class Handler(BaseHTTPRequestHandler):
    """Handle the two endpoints the harness needs: /health and chat completions."""

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path.rstrip("/") == "/health":
            self._send_json(200, {"status": "ok"})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path.rstrip("/") != "/v1/chat/completions":
            self._send_json(404, {"error": "not found"})
            return
        # Drain the request body (contents are irrelevant to the mock).
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length:
            self.rfile.read(length)
        self._send_json(
            200,
            {
                "id": "mock-cmpl-1",
                "object": "chat.completion",
                "model": "mock-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": CANNED_CONTENT},
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    def log_message(self, *args) -> None:  # keep container logs quiet
        return


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Mock OpenAI-compatible server listening on {HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

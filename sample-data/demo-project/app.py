"""Tiny demo service used to show the J.A.R.V.I.S. MCP workflow.

It intentionally contains one small bug (see test_app.py) so the demo can
show: run tests -> fail -> propose fix -> human approves -> tests pass.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


def greeting(name: str) -> str:
    return f"Hello, {name}"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            body, status = {"status": "ok"}, 200
        elif self.path.startswith("/greet/"):
            body, status = {"message": greeting(self.path.split("/greet/", 1)[1] or "world")}, 200
        else:
            body, status = {"error": "not found"}, 404
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(f"demo-api listening on :{port}", flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

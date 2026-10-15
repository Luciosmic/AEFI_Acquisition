"""
Persistent dev-time bridge server — same blocks as dev_bridge.py, but kept
warm so n8n's HTTP Request node doesn't pay a cold Python-process/import
cost on every call (each Execute Command spawn was a brand new interpreter;
this is one process, imports done once at startup).

stdlib only (http.server) — three endpoints don't justify a FastAPI/uvicorn
dependency. Revisit if the block count or request rate grows.

Usage:
    uv run python tools/n8n_workflow_poc/dev_server.py [port]   # default 8765

n8n side: HTTP Request node, GET http://127.0.0.1:8765/<block>?key=value...
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from dev_bridge import BLOCKS, call_block, coerce_value

DEFAULT_PORT = 8765


class BlockRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        block_name = parsed.path.lstrip("/")

        if block_name not in BLOCKS:
            self._send_json(404, {"error": f"unknown block '{block_name}'", "available_blocks": list(BLOCKS)})
            return

        args = {k: coerce_value(v[0]) for k, v in parse_qs(parsed.query).items()}
        try:
            result = call_block(block_name, args)
        except Exception as exc:
            self._send_json(400, {"error": str(exc)})
            return
        self._send_json(200, result)

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[dev_server] {self.address_string()} {fmt % args}")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    print(f"[dev_server] blocks available: {list(BLOCKS)}")
    print(f"[dev_server] listening on http://127.0.0.1:{port} (mocks only, no real hardware)")
    HTTPServer(("127.0.0.1", port), BlockRequestHandler).serve_forever()

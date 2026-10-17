"""Loopback-only development server; not intended as a public hosting server."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .core import run_case

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
CASE = ROOT.parent / "cases" / "001-response-lost.json"
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/styles.css": ("styles.css", "text/css; charset=utf-8")}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Avoid logging user-controlled request bodies or headers.
        pass

    def reply(self, status, body, mime="application/json; charset=utf-8"):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(raw)

    def valid_host(self):
        port = self.server.server_port
        return self.headers.get("Host") in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def do_GET(self):
        if not self.valid_host():
            return self.reply(403, {"error": "Use the loopback address printed by the server."})
        path = urlsplit(self.path).path
        if path == "/api/cases":
            return self.reply(200, [json.loads(CASE.read_text(encoding="utf-8"))])
        if path in ASSETS:
            name, mime = ASSETS[path]
            return self.reply(200, (STATIC / name).read_bytes(), mime)
        return self.reply(404, {"error": "Not found"})

    def do_POST(self):
        if not self.valid_host():
            return self.reply(403, {"error": "Invalid host"})
        allowed = {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}
        if self.headers.get("Origin") not in allowed | {None}:
            return self.reply(403, {"error": "Cross-origin execution is disabled"})
        if self.path != "/api/run":
            return self.reply(404, {"error": "Not found"})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.reply(415, {"error": "JSON required"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 4096:
                return self.reply(413, {"error": "Body must be between 1 and 4096 bytes"})
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict) or set(data) != {"mode", "inject_fault"}:
                raise ValueError("Expected mode and inject_fault only")
            if data["mode"] not in ["vulnerable", "repaired"] or type(data["inject_fault"]) is not bool:
                raise ValueError("Invalid mode or fault setting")
            return self.reply(200, run_case(**data))
        except (ValueError, TypeError, UnicodeDecodeError):
            return self.reply(400, {"error": "Invalid run configuration"})


def make_server(port=8765):
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)

#!/usr/bin/env python3
"""SKG Explorer: serves the web UI and a read-only proxy to the Solr knowledge-graph cores.

Only POST /api/<core>/rel and GET /api/<core>/ping are forwarded, so the UI never
exposes Solr's update or admin endpoints.

Env: UI_PORT (8080), UI_HOST (0.0.0.0), SOLR_URL (http://localhost:8983/solr)
"""
import json
import os
import re
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOLR_URL = os.environ.get("SOLR_URL", "http://localhost:8983/solr").rstrip("/")
CORES = {"jobs", "ecommerce", "healthcare", "support", "knowledge-graph"}
MAX_BODY = 64 * 1024
API = re.compile(r"^/api/([\w-]+)/(rel|ping)$")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)

    def send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def forward(self, url, data=None):
        headers = {"Content-Type": "application/json"} if data is not None else {}
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                status, body = resp.status, resp.read()
        except urllib.error.HTTPError as e:
            status, body = e.code, e.read()
        except urllib.error.URLError as e:
            return self.send_json(502, {"error": {"msg": f"Solr unreachable: {e.reason}", "code": 502}})
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def route(self, method):
        path = self.path.split("?")[0]
        m = API.match(path)
        if not m or m.group(1) not in CORES:
            if path.startswith("/api/"):
                self.send_json(404, {"error": {"msg": "not found", "code": 404}})
                return True
            return False
        core, action = m.groups()
        if action == "ping" and method == "GET":
            self.forward(f"{SOLR_URL}/{core}/admin/ping?wt=json")
        elif action == "rel" and method == "POST":
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > MAX_BODY:
                self.send_json(400, {"error": {"msg": "request body missing or too large", "code": 400}})
            else:
                self.forward(f"{SOLR_URL}/{core}/rel", self.rfile.read(length))
        else:
            self.send_json(405, {"error": {"msg": "method not allowed", "code": 405}})
        return True

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/healthz":
            return self.forward(f"{SOLR_URL}/jobs/admin/ping?wt=json")
        if path == "/catalog.json":
            with open(os.path.join(ROOT, "use-cases", "catalog.json"), "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return self.wfile.write(body)
        if not self.route("GET"):
            super().do_GET()

    def do_POST(self):
        if not self.route("POST"):
            self.send_json(404, {"error": {"msg": "not found", "code": 404}})


def main():
    host, port = os.environ.get("UI_HOST", "0.0.0.0"), int(os.environ.get("UI_PORT", "8080"))
    print(f"SKG Explorer listening on http://{host}:{port} (Solr: {SOLR_URL})", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Local server for the skills dashboard: python3 server.py, then open the URL it prints.

Read side: GET /api/report syncs the ledger, rebuilds the inventory (cached
for inventoryCacheSeconds) and returns the payload report.py builds.

Write side: POST /api/actions starts one of the jobs in actions.py and
returns a job id the page polls at /api/jobs/<id>. Because this server can
run `claude plugin uninstall` and move folders, three guards sit in front of
every request, each closing a different hole:
  - it binds to 127.0.0.1, so nothing else on the network reaches it;
  - the Host header must name this server, which defeats DNS rebinding
    (a hostile domain re-pointed at 127.0.0.1);
  - a POST must carry the per-run token embedded in the page, and any Origin
    header must be this server. Another site open in your browser can send a
    request here but cannot read the page to learn the token.
"""

import sys

sys.dont_write_bytecode = True

import json
import secrets
import threading
import time
import traceback
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from actions import ACTIONS, ActionError
from config import TOOL_DIR, load_config
from inventory import build_inventory
from ledger import sync
from cloud_pull import pull as pull_cloud
from report import build_report

CFG = load_config()
TOKEN = secrets.token_urlsafe(32)
TOKEN_PLACEHOLDER = "{{DASHBOARD_TOKEN}}"
# --sample shows fixtures/sample-report.json (made-up, read-only) instead of this
# machine's data: for previewing the page where there's no history, e.g. a cloud session.
SAMPLE = TOOL_DIR / "fixtures" / "sample-report.json" if "--sample" in sys.argv else None
TOKEN_HEADER = "X-Dashboard-Token"
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                 ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".json": "application/json"}

JOBS = {}
LOCKS = {"skills": threading.Lock(), "mcp": threading.Lock(), "groups": threading.Lock()}
INVENTORY = {"records": None, "meta": None, "at": 0.0}
INVENTORY_LOCK = threading.Lock()


def inventory(force_remote=False):
    ttl = CFG["server"]["inventoryCacheSeconds"]
    with INVENTORY_LOCK:
        if force_remote or INVENTORY["records"] is None or time.time() - INVENTORY["at"] > ttl:
            INVENTORY["records"], INVENTORY["meta"] = build_inventory(CFG, force_remote=force_remote)
            INVENTORY["at"] = time.time()
        return INVENTORY["records"], INVENTORY["meta"]


def invalidate():
    with INVENTORY_LOCK:
        INVENTORY["records"] = None


def start_job(action, target):
    fn, lock_name = ACTIONS[action]
    job = {"id": uuid.uuid4().hex, "action": action, "target": target, "status": "queued",
           "log": [], "result": None, "error": None, "startedAt": None, "endedAt": None}
    JOBS[job["id"]] = job

    def run():
        with LOCKS[lock_name]:
            job["status"], job["startedAt"] = "running", time.time()
            try:
                job["result"] = fn(CFG, target, job["log"].append)
                job["status"] = "done"
            except ActionError as exc:
                job["status"], job["error"] = "failed", str(exc)
            except Exception as exc:  # a crash is reported to the page, not swallowed
                job["status"], job["error"] = "failed", f"{type(exc).__name__}: {exc}"
                job["log"].append(traceback.format_exc())
            finally:
                job["endedAt"] = time.time()
                invalidate()

    threading.Thread(target=run, daemon=True).start()
    return job


class Handler(BaseHTTPRequestHandler):
    server_version = "SkillDashboard"

    def log_message(self, fmt, *args):  # quiet by default; errors still surface as responses
        pass

    # ── guards ──
    def _allowed_hosts(self):
        port = CFG["server"]["port"]
        return {f"{CFG['server']['host']}:{port}", f"localhost:{port}", f"127.0.0.1:{port}"}

    def _host_ok(self):
        return self.headers.get("Host") in self._allowed_hosts()

    def _origin_ok(self):
        origin = self.headers.get("Origin")
        return origin is None or origin in {f"http://{h}" for h in self._allowed_hosts()}

    # ── responses ──
    def _send(self, status, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(data)

    def _static(self, rel):
        web = CFG["paths"]["web"].resolve()
        path = (web / rel).resolve()
        if web not in path.parents or not path.is_file():
            return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
        body = path.read_bytes()
        if path.name == "index.html":
            body = body.replace(TOKEN_PLACEHOLDER.encode(), TOKEN.encode())
        self._send(HTTPStatus.OK, body, CONTENT_TYPES.get(path.suffix, "application/octet-stream"))

    # ── routes ──
    def do_GET(self):
        if not self._host_ok():
            return self._send(HTTPStatus.FORBIDDEN, {"error": "unexpected host"})
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            return self._static("index.html")
        if url.path.startswith("/web/"):
            return self._static(url.path[len("/web/"):])
        if url.path == "/api/report" and SAMPLE:
            return self._send(HTTPStatus.OK, json.loads(SAMPLE.read_text()))
        if url.path == "/api/report":
            refresh = parse_qs(url.query).get("refresh") == ["1"]
            result = sync(CFG)
            if refresh:  # "Check for updates" also fetches cloud-session usage
                try:
                    pull_cloud(CFG, log=lambda m: None)
                except Exception:
                    pass  # offline or no key: show what's already here
            records, meta = inventory(force_remote=refresh)
            return self._send(HTTPStatus.OK, build_report(CFG, records, meta, result))
        if url.path.startswith("/api/jobs/"):
            job = JOBS.get(url.path.rsplit("/", 1)[-1])
            return self._send(HTTPStatus.OK, job) if job else self._send(HTTPStatus.NOT_FOUND, {"error": "no such job"})
        self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self):
        if SAMPLE:
            return self._send(HTTPStatus.FORBIDDEN, {"error": "the sample is read-only"})
        if not self._host_ok() or not self._origin_ok():
            return self._send(HTTPStatus.FORBIDDEN, {"error": "unexpected host or origin"})
        if not secrets.compare_digest(self.headers.get(TOKEN_HEADER, ""), TOKEN):
            return self._send(HTTPStatus.FORBIDDEN, {"error": "missing or wrong token — reload the page"})
        if urlparse(self.path).path != "/api/actions":
            return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
        try:
            length = min(int(self.headers.get("Content-Length", 0)), CFG["server"]["maxBodyBytes"])
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._send(HTTPStatus.BAD_REQUEST, {"error": "body must be JSON"})
        action, target = body.get("action"), body.get("target")
        if action not in ACTIONS or not isinstance(target, (str, dict, type(None))):
            return self._send(HTTPStatus.BAD_REQUEST, {"error": f"unknown action {action!r}"})
        self._send(HTTPStatus.ACCEPTED, start_job(action, target))


def main():
    host, port = CFG["server"]["host"], CFG["server"]["port"]
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.daemon_threads = True
    print(f"Skills dashboard: http://{host}:{port}" + (" (sample data, read-only)" if SAMPLE else ""), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

"""Localhost HTTP server for Novi: JSON API, app shell and feature assets. Python stdlib only.

Binds to 127.0.0.1 only, rejects any Host header other than 127.0.0.1 or localhost on the chosen port, rejects
cross-origin Origin headers, and accepts POST only as application/json.
"""
from __future__ import annotations

import argparse
import importlib
import json
import mimetypes
import os
import pkgutil
import sys
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from novi import features as features_pkg
from novi import registry, storage

HERE = Path(__file__).resolve().parent
STATIC_DIR = HERE / "static"
FEATURES_DIR = HERE / "features"
DEFAULT_PORT = 8765
MAX_BODY = 1_000_000

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}

# Only the page itself needs this; it allows the app's own scripts and styles plus the Google Fonts stylesheet.
PAGE_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
)


class BadBody(Exception):
    pass


def load_features() -> None:
    """Import every feature subpackage; each one registers itself at import time."""
    for mod in pkgutil.iter_modules(features_pkg.__path__):
        if mod.ispkg:
            importlib.import_module(f"novi.features.{mod.name}")


def _status(me: Path) -> dict:
    has_data = me.exists() and any(me.iterdir())
    return {"has_profile": (me / "profile.md").exists(), "has_data": has_data}


def _content_type(path: Path) -> str:
    return CONTENT_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def make_handler(me_dir: Path) -> type[BaseHTTPRequestHandler]:
    load_features()
    me_path = Path(me_dir)

    class Handler(BaseHTTPRequestHandler):
        server_version = "novi"
        sys_version = ""

        def log_message(self, format, *args):  # keep the terminal quiet
            pass

        # --- guards -------------------------------------------------------

        def _host_allowed(self) -> bool:
            port = self.server.server_address[1]
            return self.headers.get("Host", "") in (f"127.0.0.1:{port}", f"localhost:{port}")

        def _origin_allowed(self) -> bool:
            # A browser sends Origin on cross-site requests; only our own page may send one.
            origin = self.headers.get("Origin")
            if origin is None:
                return True
            port = self.server.server_address[1]
            return origin in (f"http://127.0.0.1:{port}", f"http://localhost:{port}")

        def _json_request(self) -> bool:
            ctype = (self.headers.get("Content-Type") or "").strip().lower()
            return ctype.startswith("application/json")

        # --- responses ----------------------------------------------------

        def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, data) -> None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self._send(code, body, "application/json; charset=utf-8")

        def _error(self, code: int, message: str) -> None:
            self._json(code, {"error": message})

        # --- dispatch -----------------------------------------------------

        def do_GET(self) -> None:
            self._dispatch("GET")

        def do_POST(self) -> None:
            self._dispatch("POST")

        def _reject(self, code: int, message: str) -> None:
            # Read the small body first: answering before it is read resets the connection
            # while the client is still sending, and the client never sees the status.
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            if 0 < length <= MAX_BODY:
                self.rfile.read(length)
            self._error(code, message)

        def _dispatch(self, method: str) -> None:
            if not self._host_allowed():
                return self._reject(403, "Novi only answers on 127.0.0.1 or localhost.")
            if not self._origin_allowed():
                return self._reject(403, "Requests from other websites are not allowed.")
            if method == "POST" and not self._json_request():
                return self._reject(415, "Send Novi requests as application/json.")
            path = urlsplit(self.path).path
            if path.startswith("/api/"):
                return self._api(method, path)
            if method != "GET":
                return self._error(405, "Method not allowed.")
            if path.startswith("/features/"):
                return self._feature_file(path)
            return self._shell_file(path)

        # --- API ----------------------------------------------------------

        def _api(self, method: str, path: str) -> None:
            if method == "GET" and path == "/api/features":
                return self._json(200, [{"name": f["name"], "tab": f["tab"]} for f in registry.features()])
            if method == "GET" and path == "/api/status":
                return self._json(200, _status(me_path))

            key = f"{method} {path}"
            fn = next((f["routes"][key] for f in registry.features() if key in f["routes"]), None)
            if fn is None:
                return self._error(404, "No such API route.")
            try:
                body = self._read_body() if method == "POST" else None
            except BadBody as e:
                return self._error(400, str(e))
            try:
                result = fn(body)
            except ValueError as e:
                return self._error(400, str(e))
            except storage.StorageError as e:
                return self._error(500, str(e))
            except Exception as e:  # a feature bug must not kill the server
                traceback.print_exc()
                return self._error(500, f"Unexpected error: {e}")
            return self._json(200, result)

        def _read_body(self) -> dict:
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError as e:
                raise BadBody("Bad Content-Length.") from e
            if length > MAX_BODY:
                raise BadBody("Request body too large.")
            raw = self.rfile.read(length) if length else b""
            if not raw.strip():
                return {}
            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                raise BadBody("Request body must be JSON.") from e
            if not isinstance(data, dict):
                raise BadBody("Request body must be a JSON object.")
            return data

        # --- files --------------------------------------------------------

        def _serve_under(self, base: Path, rel: str) -> None:
            rel = unquote(rel).lstrip("/") or "index.html"
            try:
                base_resolved = base.resolve()
                target = (base_resolved / rel).resolve()
                target.relative_to(base_resolved)  # refuses ../ escapes
                if not target.is_file():
                    raise FileNotFoundError(rel)
                data = target.read_bytes()
            except (OSError, ValueError):
                return self._error(404, "Not found.")
            extra = {"Content-Security-Policy": PAGE_CSP} if target.suffix.lower() == ".html" else None
            return self._send(200, data, _content_type(target), extra)

        def _shell_file(self, path: str) -> None:
            self._serve_under(STATIC_DIR, path)

        def _feature_file(self, path: str) -> None:
            # /features/<name>/<file>, served from app/novi/features/<name>/static/
            parts = path.split("/", 3)  # ["", "features", name, rest]
            if len(parts) < 4 or not parts[3]:
                return self._error(404, "Not found.")
            name = parts[2]
            if not any(f["name"] == name for f in registry.features()):
                return self._error(404, "Not found.")
            self._serve_under(FEATURES_DIR / name / "static", parts[3])

    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="novi", description="Run the Novi tracker on this computer only.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="port on 127.0.0.1 (default 8765)")
    parser.add_argument("--me", default=None, help="your data folder (default: me/ in this repo)")
    parser.add_argument("--no-open", action="store_true", help="do not open a browser window")
    args = parser.parse_args(argv)

    if args.me:
        os.environ["NOVI_ME"] = str(Path(args.me).expanduser().resolve())
    me = storage.me_dir()
    load_features()

    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(me))
    except OSError as e:
        print(f"Could not start on 127.0.0.1:{args.port} ({e}). Is Novi already running?", file=sys.stderr)
        return 1

    url = f"http://127.0.0.1:{args.port}/"
    print(f"Novi is running at {url}  (Ctrl+C to stop)")
    if not args.no_open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0

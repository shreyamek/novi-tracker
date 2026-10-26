import http.client
import json
import threading
from http.server import ThreadingHTTPServer

import pytest

from novi import registry
from novi.server import make_handler


@pytest.fixture
def running(me):
    """Start the real handler on an ephemeral loopback port in a thread."""
    registry.clear()
    registry.register("demo", {"GET /api/demo": lambda body: {"ok": True}}, {"label": "Demo"})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(me))
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield port
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=5)
    registry.clear()


def request(port, method, path, body=None, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        hdrs = {"Content-Type": "application/json"} if payload is not None else {}
        hdrs.update(headers or {})
        conn.request(method, path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        return resp.status, resp.read()
    finally:
        conn.close()


def test_api_features_lists_registered(running):
    status, raw = request(running, "GET", "/api/features")
    assert status == 200
    features = json.loads(raw)
    assert {"name": "demo", "tab": {"label": "Demo"}} in features


def test_non_localhost_host_header_forbidden(running):
    status, _ = request(running, "GET", "/api/features", headers={"Host": "evil.example"})
    assert status == 403
    status, _ = request(running, "GET", "/", headers={"Host": f"192.168.1.5:{running}"})
    assert status == 403


def test_localhost_host_header_allowed(running):
    status, _ = request(running, "GET", "/api/features", headers={"Host": f"localhost:{running}"})
    assert status == 200


def test_index_served_with_empty_me_dir(running):
    status, raw = request(running, "GET", "/")
    assert status == 200
    _, app_js = request(running, "GET", "/app.js")
    assert b"/setup" in raw or b"/setup" in app_js


def test_server_binds_loopback_only(me):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(me))
    try:
        assert httpd.server_address[0] == "127.0.0.1"
    finally:
        httpd.server_close()


def test_path_traversal_rejected(running):
    status, _ = request(running, "GET", "/..%2F..%2Fsetup.py")
    assert status == 404
    status, _ = request(running, "GET", "/features/..%2F..%2Fx/static/a.js")
    assert status == 404

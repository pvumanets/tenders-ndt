#!/usr/bin/env python3
"""HTTP fetch relay for Scout scrape workers — runs on north-hub VPS.

Auth: Authorization: Bearer <HTTP_RELAY_SECRET or MAIL_RELAY_SECRET>
POST /fetch JSON:
  {"url","method","headers","cookies","body_b64"}
Allowlist: b2b-center.ru, *.rts-tender.ru
"""
from __future__ import annotations

import base64
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import httpx

ENV_PATH = Path("/opt/north-hub/.env")
LISTEN = ("0.0.0.0", 8798)
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
_ALLOWED = frozenset(
    {
        "www.b2b-center.ru",
        "b2b-center.ru",
        "www.rosatom.rts-tender.ru",
        "rosatom.rts-tender.ru",
    }
)
_MAX_BODY = 8_000_000


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


ENV = load_env(ENV_PATH)
SECRET = (
    (ENV.get("HTTP_RELAY_SECRET") or os.environ.get("HTTP_RELAY_SECRET") or "").strip()
    or (ENV.get("MAIL_RELAY_SECRET") or os.environ.get("MAIL_RELAY_SECRET") or "").strip()
)


def host_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    if host in _ALLOWED:
        return True
    return host.endswith(".rts-tender.ru") or host.endswith(".b2b-center.ru")


def do_fetch(payload: dict) -> dict:
    url = str(payload.get("url") or "").strip()
    if not url or not host_allowed(url):
        raise ValueError("host_denied")
    method = str(payload.get("method") or "GET").upper()
    if method not in {"GET", "HEAD", "POST"}:
        raise ValueError("method_denied")
    headers = payload.get("headers") or {}
    if not isinstance(headers, dict):
        raise ValueError("bad_headers")
    cookies = payload.get("cookies") or {}
    if not isinstance(cookies, dict):
        raise ValueError("bad_cookies")
    body_b64 = payload.get("body_b64")
    content = base64.b64decode(body_b64) if body_b64 else None
    hdrs = {"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"}
    for key, val in headers.items():
        if key.lower() in {"host", "content-length", "transfer-encoding"}:
            continue
        hdrs[str(key)] = str(val)
    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        response = client.request(method, url, headers=hdrs, cookies=cookies, content=content)
    body = response.content
    if len(body) > _MAX_BODY:
        raise ValueError("body_too_large")
    out_headers = {
        k: v
        for k, v in response.headers.items()
        if k.lower() in {"content-type", "location", "set-cookie"}
    }
    return {
        "ok": True,
        "status_code": response.status_code,
        "final_url": str(response.url),
        "headers": out_headers,
        "body_b64": base64.b64encode(body).decode("ascii"),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            self._json(200, {"ok": True, "service": "scout-http-relay"})
            return
        self._json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/fetch":
            self._json(404, {"ok": False, "error": "not_found"})
            return
        if not SECRET:
            self._json(503, {"ok": False, "error": "relay_unconfigured"})
            return
        auth = self.headers.get("Authorization") or ""
        if auth != f"Bearer {SECRET}":
            self._json(401, {"ok": False, "error": "unauthorized"})
            return
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0 or length > 500_000:
            self._json(400, {"ok": False, "error": "bad_body"})
            return
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._json(400, {"ok": False, "error": "bad_json"})
            return
        try:
            result = do_fetch(data)
        except ValueError as exc:
            self._json(400, {"ok": False, "error": str(exc)})
            return
        except Exception as exc:  # noqa: BLE001
            self._json(502, {"ok": False, "error": type(exc).__name__})
            return
        self._json(200, result)


def main() -> None:
    if not SECRET:
        print("HTTP_RELAY_SECRET / MAIL_RELAY_SECRET missing", file=sys.stderr)
        raise SystemExit(1)
    httpd = ThreadingHTTPServer(LISTEN, Handler)
    print(f"scout-http-relay on {LISTEN[0]}:{LISTEN[1]}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()

"""Convert Netscape cookie jars for Playwright contexts."""
from __future__ import annotations

from pathlib import Path

from app.worker.cookies import parse_netscape_cookies


def netscape_to_playwright(path: Path) -> list[dict]:
    out: list[dict] = []
    for item in parse_netscape_cookies(path):
        domain = str(item.get("domain") or "").strip()
        name = str(item.get("name") or "").strip()
        if not domain or not name:
            continue
        cookie: dict = {
            "name": name,
            "value": str(item.get("value") or ""),
            "domain": domain.lstrip("."),
            "path": str(item.get("path") or "/"),
        }
        if item.get("secure"):
            cookie["secure"] = True
        if item.get("httpOnly"):
            cookie["httpOnly"] = True
        out.append(cookie)
    return out

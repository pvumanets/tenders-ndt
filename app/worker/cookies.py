"""Load Netscape cookie file into Playwright cookie dicts."""
from __future__ import annotations

from pathlib import Path


def parse_netscape_cookies(path: Path) -> list[dict]:
    cookies: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        domain, _flag, cookie_path, secure, expires, name, value = parts[:7]
        cookie: dict = {
            "name": name,
            "value": value,
            "domain": domain.lstrip("."),
            "path": cookie_path or "/",
        }
        if domain.startswith("."):
            cookie["domain"] = domain
        try:
            exp = int(expires)
            if exp > 0:
                cookie["expires"] = exp
        except ValueError:
            pass
        cookie["secure"] = secure.upper() == "TRUE"
        cookies.append(cookie)
    return cookies

"""Netscape cookie jar: parse, LOCOR JSON convert, bind-safe write."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class CookieConvertError(ValueError):
    """Raised when LOCOR JSON cannot become a Netscape jar."""


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


def json_locor_to_netscape(items: Any) -> str:
    """Convert Get cookies.txt / LOCOR JSON array → Netscape HTTP Cookie File text."""
    if not isinstance(items, list):
        raise CookieConvertError("invalid_cookies_json")
    if len(items) == 0:
        raise CookieConvertError("empty_cookies")

    lines = [
        "# Netscape HTTP Cookie File",
        "# https://curl.se/docs/http-cookies.html",
        "",
    ]
    for item in items:
        if not isinstance(item, dict):
            raise CookieConvertError("invalid_cookies_json")
        domain = str(item.get("domain") or "").strip()
        name = str(item.get("name") or "").strip()
        if item.get("value") is None:
            raise CookieConvertError("invalid_cookies_json")
        value = str(item.get("value"))
        if not domain or not name or value == "":
            raise CookieConvertError("invalid_cookies_json")

        cookie_path = str(item.get("path") or "/").strip() or "/"
        secure = "TRUE" if item.get("secure") else "FALSE"
        flag = "TRUE" if domain.startswith(".") else "FALSE"
        raw_exp = item.get("expirationDate")
        if raw_exp is None:
            expires = "0"
        else:
            try:
                expires = str(int(float(raw_exp)))
            except (TypeError, ValueError) as exc:
                raise CookieConvertError("invalid_cookies_json") from exc

        lines.append(
            f"{domain}\t{flag}\t{cookie_path}\t{secure}\t{expires}\t{name}\t{value}"
        )
    return "\n".join(lines) + "\n"


def write_netscape_cookies(path: Path, text: str) -> None:
    """Write jar in place (same inode) so Docker file bind mounts stay valid."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())

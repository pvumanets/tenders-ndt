#!/usr/bin/env python3
"""Fetch / normalize platform icons into app/web/public/platforms/{id}.png (32×32).

Dev-only. Does not run in the browser. On fetch failure writes initials placeholder.
"""

from __future__ import annotations

import io
import struct
import zlib
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "app" / "web" / "public" / "platforms"
SIZE = 32

# id -> (label initials source, primary favicon host)
PLATFORMS: list[tuple[str, str, str]] = [
    ("b2b-center", "B2B", "https://www.b2b-center.ru/favicon.ico"),
    ("rostender", "РТ", "https://rostender.info/favicon.ico"),
    ("onlinecontract", "OC", "https://onlinecontract.ru/favicon.ico"),
    ("rts-rosatom", "РТС", "https://www.rosatom.rts-tender.ru/favicon.ico"),
    ("sibur-srm", "СИБ", "https://srm.sibur.ru/favicon.ico"),
    ("tender-pro", "TP", "https://www.tender.pro/favicon.ico"),
    ("tektorg-kim", "ТЭК", "https://kim.tektorg.ru/favicon.ico"),
    ("astgoz", "АСТ", "https://223.astgoz.ru/favicon.ico"),
    ("roseltorg", "РЭ", "https://www.roseltorg.ru/favicon.ico"),
    ("oilb2bcs", "OIL", "https://oilb2bcs.ru/favicon.ico"),
    ("gpb-etp", "ГПБ", "https://etp.gpb.ru/favicon.ico"),
    ("tmk", "ТМК", "https://zakupki.tmk-group.com/favicon.ico"),
    ("severstal", "СЕВ", "https://procurement.severstal.com/favicon.ico"),
]

# Soft brand-ish fills for placeholders (not purple-on-white kit)
PLACEHOLDER_COLORS: dict[str, tuple[int, int, int]] = {
    "b2b-center": (0x1A, 0x56, 0x9B),
    "rostender": (0xC4, 0x39, 0x2B),
    "onlinecontract": (0x0D, 0x6E, 0x6E),
    "rts-rosatom": (0x1B, 0x4F, 0x72),
    "sibur-srm": (0x00, 0x6B, 0x3F),
    "tender-pro": (0xE6, 0x7E, 0x22),
    "tektorg-kim": (0x2C, 0x3E, 0x50),
    "astgoz": (0x5D, 0x4E, 0x37),
    "roseltorg": (0x1F, 0x61, 0x8D),
    "oilb2bcs": (0x4A, 0x55, 0x6B),
    "gpb-etp": (0x00, 0x4B, 0x87),
    "tmk": (0x8B, 0x1E, 0x1E),
    "severstal": (0x2E, 0x40, 0x57),
}


def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_solid_png(path: Path, rgb: tuple[int, int, int], initials: str) -> None:
    """Minimal PNG + optional Pillow text overlay."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGBA", (SIZE, SIZE), (*rgb, 255))
        draw = ImageDraw.Draw(img)
        text = initials[:3]
        try:
            font = ImageFont.truetype("arial.ttf", 10 if len(text) > 2 else 12)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((SIZE - tw) / 2, (SIZE - th) / 2 - 1), text, fill=(255, 255, 255, 255), font=font)
        img.save(path, format="PNG")
        return
    except ImportError:
        pass

    # Raw RGBA solid square without text
    raw = b"".join(b"\x00" + bytes([rgb[0], rgb[1], rgb[2], 255]) * SIZE for _ in range(SIZE))
    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b"")
    path.write_bytes(png)


def fetch_bytes(url: str, timeout: float = 12.0) -> bytes | None:
    req = Request(url, headers={"User-Agent": "ndt-tender-scout-icon-fetch/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            if not data or len(data) < 16:
                return None
            return data
    except (HTTPError, URLError, TimeoutError, OSError):
        return None


def normalize_to_png(data: bytes, path: Path) -> bool:
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(data))
        img = img.convert("RGBA")
        img = img.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
        img.save(path, format="PNG")
        return True
    except Exception:
        return False


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for pid, initials, url in PLATFORMS:
        out = OUT_DIR / f"{pid}.png"
        data = fetch_bytes(url)
        ok = bool(data) and normalize_to_png(data, out)
        if not ok:
            # Try apple-touch / common paths on same origin
            base = url.rsplit("/", 1)[0]
            for alt in (
                f"{base}/apple-touch-icon.png",
                f"{base}/apple-touch-icon-precomposed.png",
                f"{base}/favicon.png",
            ):
                data = fetch_bytes(alt)
                if data and normalize_to_png(data, out):
                    ok = True
                    break
        if ok:
            print(f"OK   {pid} <- {url}")
        else:
            write_solid_png(out, PLACEHOLDER_COLORS[pid], initials)
            print(f"FALL {pid} placeholder ({initials})")


if __name__ == "__main__":
    main()

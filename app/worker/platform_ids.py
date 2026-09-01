"""Stable inbox keys: {platform_id}:{native_id} and safe docs volume dirs."""
from __future__ import annotations

from pathlib import Path

PLATFORM_ROSTENDER = "rostender"
PLATFORM_TENDER_PRO = "tender-pro"
PLATFORM_ROSELTORG = "roseltorg"
PLATFORM_B2B_CENTER = "b2b-center"
PLATFORM_RTS_ROSATOM = "rts-rosatom"
PLATFORM_OILB2BCS = "oilb2bcs"
PLATFORM_SIBUR_SRM = "sibur-srm"

_VOLUME_SEP = "__"


def compose_tender_id(platform_id: str, native_id: str) -> str:
    native = str(native_id).strip()
    platform = str(platform_id).strip()
    if not native:
        raise ValueError("empty_native_id")
    if not platform:
        raise ValueError("empty_platform_id")
    if ":" in native:
        return native if native.startswith(f"{platform}:") else f"{platform}:{native}"
    return f"{platform}:{native}"


def split_tender_id(tender_id: str) -> tuple[str | None, str]:
    text = str(tender_id).strip()
    if ":" not in text:
        return None, text
    platform, native = text.split(":", 1)
    return platform or None, native


def ensure_prefixed(tender_id: str, platform_id: str) -> str:
    platform, native = split_tender_id(tender_id)
    if platform:
        return compose_tender_id(platform, native)
    return compose_tender_id(platform_id, native)


def prefix_rows(rows: list[dict], platform_id: str) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        item = dict(row)
        tid = str(item.get("tender_id") or "").strip()
        if tid:
            item["tender_id"] = ensure_prefixed(tid, platform_id)
        item.setdefault("source_platform_id", platform_id)
        out.append(item)
    return out


def volume_dir_name(tender_id: str) -> str | None:
    """Map DB tender_id to a filesystem-safe directory name (':' → '__')."""
    text = str(tender_id).strip().replace("\\", "/").split("/")[-1]
    if not text or text in {".", ".."}:
        return None
    encoded = text.replace(":", _VOLUME_SEP, 1)
    if any(ch in encoded for ch in '<>:"/\\|?*') or "\x00" in encoded:
        return None
    return encoded[:240]


def rename_legacy_docs_dirs(root: Path) -> int:
    """Rename bare rostender dirs (digits) to rostender__{id}. Returns rename count."""
    base = Path(root)
    if not base.is_dir():
        return 0
    renamed = 0
    for child in list(base.iterdir()):
        if not child.is_dir():
            continue
        name = child.name
        if ":" in name or _VOLUME_SEP in name:
            continue
        if not name.isdigit():
            continue
        dest_name = volume_dir_name(compose_tender_id(PLATFORM_ROSTENDER, name))
        if dest_name is None:
            continue
        target = base / dest_name
        if target.exists():
            continue
        child.rename(target)
        renamed += 1
    return renamed

"""Bitrix24 REST helpers for Scout leads. Never log webhook URL or secrets."""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

log = logging.getLogger("uvicorn.error")

SOURCE_ID_DEFAULT = "TENDERS_UMANETS"
CHAT_TENDERY_DEFAULT = "chat7543"

UF_DEADLINE = "UF_CRM_1788934584"
UF_LOT_URL = "UF_CRM_1788934648"
UF_INN = "UF_CRM_1788934669"
UF_GEO = "UF_CRM_1788934700"
UF_TENDER_ID = "UF_CRM_1788934713"

PLATFORM_LABELS: dict[str, str] = {
    "rostender": "РосТендер",
    "tender-pro": "Tender.Pro",
    "roseltorg": "Росэлторг",
    "b2b-center": "B2B-Center",
    "rts-rosatom": "РТС (Росатом)",
    "oilb2bcs": "OilB2B",
    "sibur-srm": "СИБУР SRM",
}


class BitrixConfigError(RuntimeError):
    pass


class BitrixApiError(RuntimeError):
    def __init__(self, message: str, *, code: str = "bitrix_error") -> None:
        super().__init__(message)
        self.code = code


def webhook_base() -> str:
    raw = (os.getenv("BITRIX_WEBHOOK_URL") or "").strip()
    if not raw:
        raise BitrixConfigError("bitrix_unconfigured")
    return raw if raw.endswith("/") else raw + "/"


def source_id() -> str:
    return (os.getenv("BITRIX_LEAD_SOURCE_ID") or SOURCE_ID_DEFAULT).strip() or SOURCE_ID_DEFAULT


def chat_dialog_id() -> str:
    return (os.getenv("BITRIX_CHAT_DIALOG_ID") or CHAT_TENDERY_DEFAULT).strip() or CHAT_TENDERY_DEFAULT


def assigned_by_id() -> str | None:
    raw = (os.getenv("BITRIX_ASSIGNED_BY_ID") or "").strip()
    return raw or None


def public_origin() -> str:
    return (os.getenv("SCOUT_PUBLIC_ORIGIN") or "https://tenders.ndtexam.ru").strip().rstrip("/")


def platform_label(platform_id: str | None) -> str:
    key = (platform_id or "").strip()
    return PLATFORM_LABELS.get(key, key or "не указана")


def call_method(method: str, params: dict[str, Any]) -> Any:
    """POST webhook method. Never include webhook path in raised messages."""
    base = webhook_base()
    endpoint = urllib.parse.urljoin(base, f"{method}.json")
    data = urllib.parse.urlencode(params, doseq=True).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")[:300]
        log.warning("bitrix_http_error method=%s status=%s", method, exc.code)
        raise BitrixApiError(f"http_{exc.code}", code="bitrix_http") from exc
    except urllib.error.URLError as exc:
        log.warning("bitrix_url_error method=%s", method)
        raise BitrixApiError("url_error", code="bitrix_unreachable") from exc
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise BitrixApiError("bad_json", code="bitrix_bad_json") from exc
    if payload.get("error"):
        log.warning(
            "bitrix_api_error method=%s error=%s",
            method,
            payload.get("error"),
        )
        raise BitrixApiError(
            str(payload.get("error_description") or payload.get("error")),
            code="bitrix_error",
        )
    return payload.get("result")

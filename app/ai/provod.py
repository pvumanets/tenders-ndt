"""provod.ai OpenAI-compatible client for P10 AI tier review."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Callable

import httpx

PROVOD_BASE_URL = os.environ.get("PROVOD_BASE_URL", "https://api.provod.ai").rstrip("/")
PRIMARY_MODEL = "claude-sonnet-4-6"
FALLBACK_MODEL = "openai-gpt-5-4"
_TIERS = frozenset({"L1", "L2", "L3"})

_SYSTEM = """Ты классификатор закупок НК (неразрушающий контроль) для лаборатории услуг.
Верни ТОЛЬКО JSON: {"tier":"L1"|"L2"|"L3","reason_ru":"..."}.
Правила:
- Явная услуга проведения НК / контроля сварных / трубопроводов / толщины стенок → L1 или L2.
- Поставка / закупка оборудования, приборов, калибровка, расходники → L3 (Смотреть).
- Обучение / аттестация / нерелевант → L3 (не Горячие).
Запрещено учитывать класс опасности и допуски.
Не пиши ничего кроме JSON."""


@dataclass(frozen=True)
class AiTierResult:
    tier: str
    reason_ru: str
    model: str


class AiTierError(Exception):
    """provod.ai transport or parse failure."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def provod_api_key() -> str | None:
    key = os.environ.get("PROVOD_API_KEY", "").strip()
    return key or None


def _parse_json_content(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise AiTierError("empty_response")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            raise AiTierError("invalid_json") from None
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise AiTierError("invalid_json")
    tier = str(data.get("tier") or "").strip()
    reason = str(data.get("reason_ru") or "").strip()
    if tier not in _TIERS or not reason:
        raise AiTierError("invalid_payload")
    return {"tier": tier, "reason_ru": reason}


def _chat_once(
    *,
    client: httpx.Client,
    key: str,
    model: str,
    user_content: str,
) -> AiTierResult:
    resp = client.post(
        f"{PROVOD_BASE_URL}/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user_content},
            ],
        },
        timeout=60.0,
    )
    if resp.status_code >= 400:
        raise AiTierError(f"http_{resp.status_code}")
    body = resp.json()
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AiTierError("bad_response_shape") from exc
    parsed = _parse_json_content(str(content))
    return AiTierResult(tier=parsed["tier"], reason_ru=parsed["reason_ru"], model=model)


def build_user_prompt(
    *,
    title: str,
    rules_tier: str,
    fit_reason: str | None = None,
    description: str | None = None,
    platform_id: str | None = None,
) -> str:
    parts = [
        f"title: {title}",
        f"rules_tier: {rules_tier}",
    ]
    if fit_reason:
        parts.append(f"fit_reason: {fit_reason}")
    if platform_id:
        parts.append(f"platform_id: {platform_id}")
    if description:
        parts.append(f"description: {description[:800]}")
    return "\n".join(parts)


def review_tier(
    *,
    title: str,
    rules_tier: str,
    fit_reason: str | None = None,
    description: str | None = None,
    platform_id: str | None = None,
    http_client: httpx.Client | None = None,
    post_chat: Callable[..., AiTierResult] | None = None,
) -> AiTierResult:
    key = provod_api_key()
    if not key:
        raise AiTierError("missing_api_key")
    prompt = build_user_prompt(
        title=title,
        rules_tier=rules_tier,
        fit_reason=fit_reason,
        description=description,
        platform_id=platform_id,
    )
    if post_chat is not None:
        try:
            return post_chat(model=PRIMARY_MODEL, user_content=prompt)
        except AiTierError:
            return post_chat(model=FALLBACK_MODEL, user_content=prompt)

    own = http_client is None
    client = http_client or httpx.Client()
    try:
        try:
            return _chat_once(client=client, key=key, model=PRIMARY_MODEL, user_content=prompt)
        except AiTierError:
            return _chat_once(client=client, key=key, model=FALLBACK_MODEL, user_content=prompt)
    finally:
        if own:
            client.close()

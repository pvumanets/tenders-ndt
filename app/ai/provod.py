"""provod.ai OpenAI-compatible client for P10 AI tier review."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Callable

import httpx

PROVOD_BASE_URL = os.environ.get("PROVOD_BASE_URL", "https://api.provod.ai").rstrip("/")
# Default aliases smoke-verified 2026-08-29 on api.provod.ai (same host only).
# Primary ~55s; fallbacks ~1–2s. Override via PROVOD_MODEL_CHAIN=a,b,c
_DEFAULT_MODEL_CHAIN = (
    "claude-sonnet-4-6",
    "openai-gpt-5-4",
    "gemini-2.5-flash",
)
PRIMARY_MODEL = _DEFAULT_MODEL_CHAIN[0]
FALLBACK_MODEL = _DEFAULT_MODEL_CHAIN[1]
_CHAT_TIMEOUT = 120.0
_TIERS = frozenset({"L1", "L2", "L3"})
_DESC_MAX = 800
# Same-model retries on transient host errors (103).
_RETRY_BACKOFFS_SEC = (2.0, 5.0)
_HOST_TRANSIENT_PREFIXES = ("http_429", "http_503", "timeout", "transport")

# SoT seed: docs/delivery/ai-master-prompt.md (accepted session 1).
# Live override: operator_settings.ai_system_prompt (092).
DEFAULT_SYSTEM_PROMPT = """Ты — опытный директор лаборатории неразрушающего контроля, которая оказывает услуги на промышленных объектах (нефтегаз, атомная и химическая промышленность, крупные стройки и реконструкции).

Сильные стороны лаборатории: визуальный и измерительный контроль (ВИК), капиллярный / цветная дефектоскопия (ПВК), ультразвуковой контроль (УЗК), акустические методы, металлография (услуги по составу и структуре металла), радиографический контроль (рентген, гамма, цифровая радиография), в том числе оценка толщины с помощью цифровой радиографии.

Задача: по фактам закупки оценить, насколько лот подходит лаборатории услуг НК, и вернуть ТОЛЬКО один JSON-объект без пояснений снаружи:
{"tier":"L1"|"L2"|"L3","reason_ru":"..."}

Смысл уровней:
- L1 (Горячие) — явный предмет: оказание услуг / проведение работ НК (или сочетание разрушающего и неразрушающего контроля) на промышленном объекте; формулировка однозначна.
- L2 (Сильные) — услуга НК просматривается, но предмет смешанный, формулировка слабее, или есть сомнение по профилю объекта (в том числе объекты железнодорожной инфраструктуры, где часто нужны особые допуски — это повод для L2, а не автоматический отказ).
- L3 (Смотреть) — поставка / закупка оборудования и приборов, расходники, поверка и калибровка средств измерений без работ контроля на объекте, обучение и аттестация персонала как основной предмет, либо закупка явно не про промышленный НК.

Ориентиры (не чеклист регулярок):
- «Поставка оборудования для НК», «дефектоскоп», «расходные материалы» → обычно L3.
- «Проведение НК», «оказание услуг по УЗК / ВИК / ПВК / РК», контроль сварных соединений, трубопроводов, конструкций на НПЗ, АЭС, химических и подобных объектах → обычно L1 или L2.
- Название метода в тексте ещё не значит услугу: если покупают прибор или материалы — это L3.
- Не решай тир по классу опасности объекта и по наличию или отсутствию допусков у лаборатории — это ручная оценка людей.
- Если описания нет — опирайся на название; если описание есть — используй его, чтобы уточнить предмет.

reason_ru: одно-два коротких предложения по-русски о предмете закупки (услуга / поставка / обучение и т.п.), без жаргона скоринга и без сравнения с другими системами оценки.

Примеры ожидаемой логики:
1) Проведение НК методом УЗК и цветной дефектоскопии сварных соединений на комплексе гидрокрекинга → L1.
2) Услуги разрушающего и неразрушающего контроля материалов и конструкций при сооружении блоков АЭС → L1.
3) Поставка оборудования для неразрушающего контроля → L3.
4) Дефектоскоп для НК стальных канатов → L3.
5) Обучение и аттестация персонала по НК → L3.
6) Услуги поверки и калибровки средств измерений → L3.
7) Контроль толщины стенок трубопроводов методом НК как услуга → L1 или L2.
8) Закупка с «неразрушающий» в названии, но предмет — медоборудование или расходники клиники → L3."""

# Back-compat alias for tests / imports
_SYSTEM = DEFAULT_SYSTEM_PROMPT


def get_default_system_prompt() -> str:
    return DEFAULT_SYSTEM_PROMPT


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


def model_chain() -> tuple[str, ...]:
    """Ordered aliases on api.provod.ai. Env PROVOD_MODEL_CHAIN overrides default."""
    raw = os.environ.get("PROVOD_MODEL_CHAIN", "").strip()
    if not raw:
        return _DEFAULT_MODEL_CHAIN
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return tuple(parts) if parts else _DEFAULT_MODEL_CHAIN


def provod_api_key() -> str | None:
    from app.api.operator_settings import resolve_provod_api_key

    return resolve_provod_api_key()


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
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise AiTierError("invalid_json") from exc
    if not isinstance(data, dict):
        raise AiTierError("invalid_json")
    tier = str(data.get("tier") or "").strip()
    reason = str(data.get("reason_ru") or "").strip()
    if tier not in _TIERS or not reason:
        raise AiTierError("invalid_payload")
    return {"tier": tier, "reason_ru": reason}


def is_host_transient_error(message: str) -> bool:
    """True for rate-limit / outage / transport — worth backoff or circuit-break."""
    msg = (message or "").strip().lower()
    return any(msg == p or msg.startswith(p + "_") or msg.startswith(p) for p in _HOST_TRANSIENT_PREFIXES)


def _call_with_same_model_retry(call: Callable[[], AiTierResult]) -> AiTierResult:
    """1–2 short backoffs on transient errors, then raise last error."""
    import time

    last: AiTierError | None = None
    attempts = 1 + len(_RETRY_BACKOFFS_SEC)
    for attempt in range(attempts):
        try:
            return call()
        except AiTierError as exc:
            last = exc
            if not is_host_transient_error(exc.message):
                raise
            if attempt >= len(_RETRY_BACKOFFS_SEC):
                raise
            time.sleep(_RETRY_BACKOFFS_SEC[attempt])
    assert last is not None
    raise last


def _chat_once(
    *,
    client: httpx.Client,
    key: str,
    model: str,
    user_content: str,
    system_prompt: str | None = None,
) -> AiTierResult:
    system = system_prompt if system_prompt is not None else DEFAULT_SYSTEM_PROMPT
    try:
        resp = client.post(
            f"{PROVOD_BASE_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
            },
            timeout=_CHAT_TIMEOUT,
        )
    except httpx.TimeoutException as exc:
        raise AiTierError("timeout") from exc
    except httpx.TransportError as exc:
        raise AiTierError("transport") from exc
    if resp.status_code >= 400:
        raise AiTierError(f"http_{resp.status_code}")
    try:
        body = resp.json()
    except json.JSONDecodeError as exc:
        raise AiTierError("invalid_json") from exc
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AiTierError("bad_response_shape") from exc
    parsed = _parse_json_content(str(content))
    return AiTierResult(tier=parsed["tier"], reason_ru=parsed["reason_ru"], model=model)


def build_user_prompt(
    *,
    title: str,
    customer_name: str | None = None,
    description: str | None = None,
) -> str:
    """Purchase facts only — never rules_tier / fit_reason / score / methods."""
    parts = [f"title: {title}"]
    cust = (customer_name or "").strip()
    if cust:
        parts.append(f"customer: {cust}")
    desc = (description or "").strip()
    if desc:
        parts.append(f"description: {desc[:_DESC_MAX]}")
    return "\n".join(parts)


def review_tier(
    *,
    title: str,
    customer_name: str | None = None,
    description: str | None = None,
    system_prompt: str | None = None,
    http_client: httpx.Client | None = None,
    post_chat: Callable[..., AiTierResult] | None = None,
) -> AiTierResult:
    key = provod_api_key()
    if not key:
        raise AiTierError("missing_api_key")
    prompt = build_user_prompt(
        title=title,
        customer_name=customer_name,
        description=description,
    )
    system = system_prompt if system_prompt is not None else DEFAULT_SYSTEM_PROMPT
    chain = model_chain()
    last_error: AiTierError | None = None

    if post_chat is not None:
        for model in chain:
            try:
                def _once(m: str = model) -> AiTierResult:
                    try:
                        return post_chat(model=m, user_content=prompt, system_prompt=system)
                    except TypeError:
                        return post_chat(model=m, user_content=prompt)

                return _call_with_same_model_retry(_once)
            except AiTierError as exc:
                last_error = exc
                continue
        assert last_error is not None
        raise last_error

    own = http_client is None
    client = http_client or httpx.Client()
    try:
        for model in chain:
            try:
                def _once(m: str = model) -> AiTierResult:
                    return _chat_once(
                        client=client,
                        key=key,
                        model=m,
                        user_content=prompt,
                        system_prompt=system,
                    )

                return _call_with_same_model_retry(_once)
            except AiTierError as exc:
                last_error = exc
                continue
        assert last_error is not None
        raise last_error
    finally:
        if own:
            client.close()

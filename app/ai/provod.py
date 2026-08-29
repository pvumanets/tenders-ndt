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
_DESC_MAX = 800

# SoT: docs/delivery/ai-master-prompt.md (accepted session 1)
_SYSTEM = """Ты — опытный директор лаборатории неразрушающего контроля, которая оказывает услуги на промышленных объектах (нефтегаз, атомная и химическая промышленность, крупные стройки и реконструкции).

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

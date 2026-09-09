"""Bitrix24 field builders for lot → lead + chat. No secrets. Brand: Разведчик."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from app.bitrix import (
    UF_DEADLINE,
    UF_GEO,
    UF_INN,
    UF_LOT_URL,
    UF_TENDER_ID,
    assigned_by_id,
    platform_label,
    public_origin,
    source_id,
)

MSK = ZoneInfo("Europe/Moscow")

TIER_CHAT_TITLE = {
    "L1": "Горячий тендер (L1)",
    "L2": "Сильный тендер (L2)",
    "L3": "Смотреть (L3)",
}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _truncate(text: str, max_len: int = 180) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def format_price_ru(price: Any) -> str:
    if price is None or price == "":
        return "не указана"
    try:
        if isinstance(price, Decimal):
            num = price
        else:
            num = Decimal(str(price))
    except Exception:  # noqa: BLE001
        return "не указана"
    quantized = num.quantize(Decimal("1"))
    raw = f"{quantized:,}".replace(",", " ")
    return f"{raw} ₽"


def format_deadline_display(deadline_msk: str | None) -> str:
    text = _clean(deadline_msk)
    if not text:
        return "не указан"
    try:
        iso = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=MSK)
        local = dt.astimezone(MSK)
        return local.strftime("%d.%m.%Y %H:%M") + " МСК"
    except ValueError:
        return text


def deadline_for_bitrix(deadline_msk: str | None) -> str | None:
    text = _clean(deadline_msk)
    if not text:
        return None
    try:
        iso = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=MSK)
        local = dt.astimezone(MSK)
        return local.strftime("%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        # date-only
        try:
            d = datetime.strptime(text[:10], "%Y-%m-%d").replace(
                hour=23, minute=59, tzinfo=MSK
            )
            return d.strftime("%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            return None


def build_comments(
    *,
    customer: str,
    inn: str,
    price_rub: Any,
    platform_id: str | None,
    tier: str,
    why: str,
    tender_id: str,
) -> str:
    """Must-visible block: Bitrix form often hides Компания/Сумма/wrong INN UF."""
    origin = public_origin()
    app_url = f"{origin}/"
    lines = [
        f"Заказчик: {_clean(customer) or 'не указан'}",
        f"ИНН: {_clean(inn) or 'не указан'}",
        f"НМЦ: {format_price_ru(price_rub)}",
        f"Площадка: {platform_label(platform_id)}",
        f"Тир: {tier}",
    ]
    why_c = _clean(why)
    if why_c:
        lines.append(f"Почему: {why_c}")
    lines.append(f"Внутренний id: {tender_id}")
    lines.append(f"Разведчик: {app_url}")
    return "\n".join(lines)


def build_lead_fields(lot: dict[str, Any]) -> dict[str, Any]:
    """Map lot dict → crm.lead.add FIELDS (flat keys)."""
    title = _clean(lot.get("title")) or "Тендер"
    customer = _clean(lot.get("customer_name")) or "не указан"
    inn = _clean(lot.get("customer_inn"))
    tier = _clean(lot.get("effective_tier") or lot.get("tier") or "L3") or "L3"
    why = _clean(lot.get("ai_reason_ru")) or _clean(lot.get("fit_reason"))
    tender_id = _clean(lot.get("tender_id"))
    price = lot.get("price_rub")
    fields: dict[str, Any] = {
        "TITLE": title,
        "COMPANY_TITLE": customer,
        "CURRENCY_ID": "RUB",
        "SOURCE_ID": source_id(),
        "COMMENTS": build_comments(
            customer=customer,
            inn=inn,
            price_rub=price,
            platform_id=_clean(lot.get("source_platform_id")) or None,
            tier=tier,
            why=why,
            tender_id=tender_id,
        ),
    }
    if price is not None and price != "":
        try:
            fields["OPPORTUNITY"] = str(Decimal(str(price)))
        except Exception:  # noqa: BLE001
            pass

    url = _clean(lot.get("url"))
    if url:
        fields[UF_LOT_URL] = url
    if inn:
        fields[UF_INN] = inn
    geo = _clean(lot.get("location"))
    if geo:
        fields[UF_GEO] = geo
    if tender_id:
        fields[UF_TENDER_ID] = tender_id
    dl = deadline_for_bitrix(
        lot.get("deadline_msk") if isinstance(lot.get("deadline_msk"), str) else None
    )
    if dl:
        fields[UF_DEADLINE] = dl

    assignee = assigned_by_id()
    if assignee:
        fields["ASSIGNED_BY_ID"] = assignee

    # Contacts — should if non-empty
    name = _clean(lot.get("contact_name"))
    if name:
        parts = name.split(None, 1)
        fields["NAME"] = parts[0]
        if len(parts) > 1:
            fields["LAST_NAME"] = parts[1]
    phone = _clean(lot.get("contact_phone"))
    if phone:
        fields["PHONE"] = [{"VALUE": phone, "VALUE_TYPE": "WORK"}]
    email = _clean(lot.get("contact_email"))
    if email:
        fields["EMAIL"] = [{"VALUE": email, "VALUE_TYPE": "WORK"}]

    return fields


def lead_fields_to_params(fields: dict[str, Any]) -> dict[str, str]:
    """Flatten for application/x-www-form-urlencoded Bitrix webhook."""
    params: dict[str, str] = {}
    for key, value in fields.items():
        if isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    for sub_k, sub_v in item.items():
                        params[f"FIELDS[{key}][{i}][{sub_k}]"] = str(sub_v)
                else:
                    params[f"FIELDS[{key}][{i}]"] = str(item)
        else:
            params[f"FIELDS[{key}]"] = str(value)
    return params


def build_chat_message(*, lot: dict[str, Any], lead_id: int | str) -> str:
    tier = _clean(lot.get("effective_tier") or lot.get("tier") or "L3") or "L3"
    header = TIER_CHAT_TITLE.get(tier, f"Тендер ({tier})")
    title = _truncate(_clean(lot.get("title")) or "Без названия")
    customer = _clean(lot.get("customer_name")) or "не указан"
    geo = _clean(lot.get("location")) or "не указано"
    deadline = format_deadline_display(
        lot.get("deadline_msk") if isinstance(lot.get("deadline_msk"), str) else None
    )
    price = format_price_ru(lot.get("price_rub"))
    platform = platform_label(_clean(lot.get("source_platform_id")) or None)
    why = _clean(lot.get("ai_reason_ru")) or _clean(lot.get("fit_reason")) or "—"
    url = _clean(lot.get("url"))
    tender_id = _clean(lot.get("tender_id"))
    origin = public_origin()

    lines = [
        f"[b]{header}[/b]",
        "--------------------",
        f"[b]{title}[/b]",
        f"Заказчик: {customer}",
        f"Где: {geo}",
        f"Срок подачи: {deadline}",
        f"НМЦ: {price}",
        f"Площадка: {platform}",
        f"Тир: {tier}",
        f"Почему: {why}",
        f"ID: {tender_id}",
        f"Лид CRM: #{lead_id}",
    ]
    if url:
        lines.append(f"[url={url}]Лот на ЭТП[/url]")
    lines.append(f"[url={origin}/]Разведчик[/url]")
    lines.append("[i]Сообщение отправлено автоматически из Разведчика.[/i]")
    return "\n".join(lines)

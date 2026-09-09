"""Unit tests for Bitrix field builders — no live webhook."""
from __future__ import annotations

from decimal import Decimal

from app.bitrix import (
    UF_DEADLINE,
    UF_GEO,
    UF_INN,
    UF_LOT_URL,
    UF_TENDER_ID,
)
from app.bitrix.fields import (
    build_chat_message,
    build_comments,
    build_lead_fields,
    format_price_ru,
    lead_fields_to_params,
)


def test_format_price_ru() -> None:
    assert format_price_ru(None) == "не указана"
    assert "1 250 000" in format_price_ru(Decimal("1250000"))


def test_build_comments_has_customer_sum_inn() -> None:
    text = build_comments(
        customer="Морпорт",
        inn="7811087784",
        price_rub=1250000,
        platform_id="rostender",
        tier="L1",
        why="УЗК рельсов",
        tender_id="rostender:1",
    )
    assert "Заказчик: Морпорт" in text
    assert "ИНН: 7811087784" in text
    assert "1 250 000" in text
    assert "Площадка: РосТендер" in text
    assert "Тир: L1" in text


def test_build_lead_fields_must_map(monkeypatch) -> None:
    monkeypatch.setenv("BITRIX_LEAD_SOURCE_ID", "TENDERS_UMANETS")
    monkeypatch.delenv("BITRIX_ASSIGNED_BY_ID", raising=False)
    fields = build_lead_fields(
        {
            "tender_id": "rostender:94804428",
            "title": "УЗК рельсов",
            "customer_name": "Морпорт",
            "customer_inn": "7811087784",
            "price_rub": 1250000,
            "deadline_msk": "2026-09-23T18:00:00+03:00",
            "url": "https://rostender.info/tender/94804428",
            "location": "СПб",
            "source_platform_id": "rostender",
            "effective_tier": "L1",
            "fit_reason": "услуги НК",
            "contact_phone": "+79990001122",
            "contact_email": "a@b.ru",
            "contact_name": "Иван Тестов",
        }
    )
    assert fields["TITLE"] == "УЗК рельсов"
    assert fields["COMPANY_TITLE"] == "Морпорт"
    assert fields["OPPORTUNITY"] == "1250000"
    assert fields["CURRENCY_ID"] == "RUB"
    assert fields["SOURCE_ID"] == "TENDERS_UMANETS"
    assert fields[UF_INN] == "7811087784"
    assert fields[UF_LOT_URL].startswith("https://")
    assert fields[UF_GEO] == "СПб"
    assert fields[UF_TENDER_ID] == "rostender:94804428"
    assert UF_DEADLINE in fields
    assert "Заказчик: Морпорт" in fields["COMMENTS"]
    assert "ИНН: 7811087784" in fields["COMMENTS"]
    assert "1 250 000" in fields["COMMENTS"]
    assert "Площадка: РосТендер" in fields["COMMENTS"]
    assert "Тир: L1" in fields["COMMENTS"]
    assert fields["PHONE"][0]["VALUE"] == "+79990001122"
    assert fields["EMAIL"][0]["VALUE"] == "a@b.ru"
    params = lead_fields_to_params(fields)
    assert params["FIELDS[TITLE]"] == "УЗК рельсов"
    assert params["FIELDS[PHONE][0][VALUE]"] == "+79990001122"


def test_build_chat_message_includes_sum_and_customer() -> None:
    msg = build_chat_message(
        lot={
            "title": "УЗК",
            "customer_name": "Морпорт",
            "price_rub": 1250000,
            "location": "СПб",
            "deadline_msk": "2026-09-23T18:00:00+03:00",
            "source_platform_id": "rostender",
            "effective_tier": "L1",
            "fit_reason": "НК",
            "tender_id": "rostender:1",
            "url": "https://example.com/t",
        },
        lead_id=6765,
    )
    assert "Горячий тендер (L1)" in msg
    assert "Морпорт" in msg
    assert "1 250 000" in msg
    assert "#6765" in msg
    assert "РосТендер" in msg

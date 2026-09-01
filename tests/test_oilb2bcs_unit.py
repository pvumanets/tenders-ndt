"""Unit: OilB2B Ext.NET payload parsing (no live HTTP)."""
from __future__ import annotations

import pytest

from app.worker import oilb2bcs
from app.worker.platform_ids import PLATFORM_OILB2BCS, compose_tender_id, prefix_rows

_EXTNET_BODY = (
    '{result:[1,[{"Id":501,"CategoryText":"Неразрушающий контроль",'
    '"CustomerText":"ООО Тест","Stop":"2026-09-15T10:00:00.000","State":"Открыта"}],'
    '[{"planclaim":501,"name":"Ультразвуковой контроль"}]]}'
)


@pytest.mark.unit
def test_parse_extnet_payload() -> None:
    parsed = oilb2bcs._parse_extnet_payload(_EXTNET_BODY)
    assert isinstance(parsed, list)
    assert parsed[0] == 1
    claims = parsed[1]
    assert claims[0]["Id"] == 501


@pytest.mark.unit
def test_rows_from_claims() -> None:
    payload = oilb2bcs._parse_extnet_payload(_EXTNET_BODY)
    assert isinstance(payload, list)
    total = int(payload[0])
    claims = payload[1]
    items = payload[2]
    assert total == 1
    rows = oilb2bcs._rows_from_claims(claims, items, base=oilb2bcs.DEFAULT_BASE)
    assert len(rows) == 1
    assert rows[0]["tender_id"] == "501"
    assert "ультразвуковой" in rows[0]["description"].lower()
    assert rows[0]["deadline_msk"] == "15.09.2026 10:00"


@pytest.mark.unit
def test_prefix_rows_oil() -> None:
    rows = prefix_rows([{"tender_id": "501", "title": "x"}], PLATFORM_OILB2BCS)
    assert rows[0]["tender_id"] == "oilb2bcs:501"
    assert compose_tender_id(PLATFORM_OILB2BCS, "501") == "oilb2bcs:501"


@pytest.mark.unit
def test_enrich_cards_noop() -> None:
    scored = [{"tender_id": "oilb2bcs:501", "title": "t", "tier": "L2"}]
    out, errors = oilb2bcs.enrich_cards(scored, ["oilb2bcs:501"])
    assert errors == []
    assert out[0].get("card_fetched") is True

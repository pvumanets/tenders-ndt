"""Unit: Sibur SRM parsers and helpers (no live Playwright)."""
from __future__ import annotations

import pytest

from app.worker import sibur_srm
from app.worker.platform_ids import PLATFORM_SIBUR_SRM, compose_tender_id, prefix_rows

_GRID = """
2138496 Запрос предложений Строительный контроль объект 123
2138500 Аукцион Неразрушающий контроль трубопроводов
000000 служебная строка
abc без номера
"""


@pytest.mark.unit
def test_is_login_page() -> None:
    assert sibur_srm.is_login_page(title="Вход в систему", body="Пользователь Пароль")
    assert not sibur_srm.is_login_page(title="NWBC", body="Поиск процедур")


@pytest.mark.unit
def test_parse_grid_text() -> None:
    rows = sibur_srm.parse_grid_text(_GRID)
    ids = [r.tender_id for r in rows]
    assert "2138496" in ids
    assert "2138500" in ids
    assert "000000" not in ids


@pytest.mark.unit
def test_prefix_rows_sibur() -> None:
    rows = prefix_rows([{"tender_id": "2138496", "title": "x"}], PLATFORM_SIBUR_SRM)
    assert rows[0]["tender_id"] == "sibur-srm:2138496"
    assert compose_tender_id(PLATFORM_SIBUR_SRM, "1") == "sibur-srm:1"


@pytest.mark.unit
def test_nwbc_search_url() -> None:
    url = sibur_srm.nwbc_search_url(base="https://srm.sibur.ru", node="0000000037")
    assert "sap-nwbc-node=0000000037" in url

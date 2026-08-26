"""Unit: clean_customer_name strips Rostender column chrome."""
from __future__ import annotations

import pytest

from app.worker.customer_name import clean_customer_name
from app.worker.list_scrape import _parse_customer
from bs4 import BeautifulSoup


@pytest.mark.unit
def test_clean_customer_name_strips_pua_and_tail() -> None:
    raw = "Заказчик\ue012\ue013 ООО «Север» Закупки заказчика Отрасль"
    assert clean_customer_name(raw) == "ООО «Север»"


@pytest.mark.unit
def test_clean_customer_name_empty_after_pua() -> None:
    assert clean_customer_name("\ue000\ue001") is None


@pytest.mark.unit
def test_parse_customer_from_list_column() -> None:
    html = """
    <article class="tender-row">
      <div class="customer-branches-column">
        Заказчик\ue012 ООО Лаб Закупки заказчика
      </div>
    </article>
    """
    art = BeautifulSoup(html, "lxml").select_one("article.tender-row")
    assert _parse_customer(art) == "ООО Лаб"

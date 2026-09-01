"""Unit: operator settings GET/PUT validation. No database required."""
from __future__ import annotations

import pytest

from app.api.operator_settings import (
    DEFAULT_L1_MIN_PRICE_RUB,
    OperatorSettingsError,
    parse_l1_min_price_rub,
    put_operator_settings,
)


@pytest.mark.unit
def test_parse_l1_min_price_rub_bounds() -> None:
    assert parse_l1_min_price_rub(0) == 0
    assert parse_l1_min_price_rub(100_000) == 100_000
    assert parse_l1_min_price_rub(5_000_000) == 5_000_000
    with pytest.raises(OperatorSettingsError, match="invalid_l1_min_price_rub"):
        parse_l1_min_price_rub(-1)
    with pytest.raises(OperatorSettingsError, match="invalid_l1_min_price_rub"):
        parse_l1_min_price_rub(5_000_001)
    with pytest.raises(OperatorSettingsError, match="invalid_l1_min_price_rub"):
        parse_l1_min_price_rub(True)
    with pytest.raises(OperatorSettingsError, match="invalid_l1_min_price_rub"):
        parse_l1_min_price_rub("100000")


@pytest.mark.unit
def test_put_operator_settings_requires_field(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.api.operator_settings.session_factory",
        lambda: (_ for _ in ()).throw(RuntimeError("database_unconfigured")),
    )
    with pytest.raises(OperatorSettingsError, match="invalid_l1_min_price_rub"):
        put_operator_settings({})
    with pytest.raises(OperatorSettingsError, match="invalid_l1_min_price_rub"):
        put_operator_settings({"l1_min_price_rub": 50_000.5})


@pytest.mark.unit
def test_default_l1_min_price_constant() -> None:
    assert DEFAULT_L1_MIN_PRICE_RUB == 100_000

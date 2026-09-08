"""Unit: tier-teach parsers (092). No TestClient (lifespan hang risk on win)."""
from __future__ import annotations

import pytest

from app.api.inbox import InboxQueryError, parse_teach_body
from app.api.main import app
from app.api.operator_settings import (
    OperatorSettingsError,
    parse_ai_system_prompt,
    put_operator_settings,
)


@pytest.mark.unit
def test_parse_teach_body_ok() -> None:
    parsed = parse_teach_body(
        {
            "from_bucket": "L2",
            "to_bucket": "L1",
            "drop_tier_correct": True,
            "reason_ru": "  услуга НК  ",
        }
    )
    assert parsed["from_bucket"] == "L2"
    assert parsed["to_bucket"] == "L1"
    assert parsed["drop_tier_correct"] is True
    assert parsed["reason_ru"] == "услуга НК"


@pytest.mark.unit
def test_parse_teach_body_expired_and_errors() -> None:
    parse_teach_body(
        {
            "from_bucket": "expired",
            "to_bucket": "L3",
            "drop_tier_correct": False,
            "reason_ru": "не наш тир",
        }
    )
    with pytest.raises(InboxQueryError, match="same_bucket"):
        parse_teach_body(
            {
                "from_bucket": "L1",
                "to_bucket": "L1",
                "drop_tier_correct": True,
                "reason_ru": "x",
            }
        )
    with pytest.raises(InboxQueryError, match="invalid_reason"):
        parse_teach_body(
            {
                "from_bucket": "L1",
                "to_bucket": "L2",
                "drop_tier_correct": True,
                "reason_ru": "   ",
            }
        )
    with pytest.raises(InboxQueryError, match="invalid_bucket"):
        parse_teach_body(
            {
                "from_bucket": "archive",
                "to_bucket": "L1",
                "drop_tier_correct": True,
                "reason_ru": "x",
            }
        )


@pytest.mark.unit
def test_tier_teach_routes_registered() -> None:
    paths = [getattr(route, "path", "") or "" for route in app.routes]
    assert "/api/inbox/{tender_id}/tier-teach" in paths
    assert "/api/tech/tier-teach" in paths


@pytest.mark.unit
def test_parse_ai_system_prompt() -> None:
    assert parse_ai_system_prompt(None) is None
    assert parse_ai_system_prompt("  hello  ") == "hello"
    with pytest.raises(OperatorSettingsError, match="invalid_ai_system_prompt"):
        parse_ai_system_prompt("")
    with pytest.raises(OperatorSettingsError, match="invalid_ai_system_prompt"):
        parse_ai_system_prompt("   ")
    with pytest.raises(OperatorSettingsError, match="invalid_ai_system_prompt"):
        parse_ai_system_prompt(123)


@pytest.mark.unit
def test_put_operator_settings_requires_any_field(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.api.operator_settings.session_factory",
        lambda: (_ for _ in ()).throw(RuntimeError("database_unconfigured")),
    )
    with pytest.raises(OperatorSettingsError, match="invalid_body"):
        put_operator_settings({})

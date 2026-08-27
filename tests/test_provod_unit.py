"""Unit: provod.ai review_tier with mock post_chat (no network)."""
from __future__ import annotations

import pytest

from app.ai.provod import AiTierError, AiTierResult, review_tier


@pytest.mark.unit
def test_review_tier_success_primary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROVOD_API_KEY", "test-key")

    def post_chat(*, model: str, user_content: str) -> AiTierResult:
        assert "title:" in user_content
        return AiTierResult(tier="L3", reason_ru="Поставка оборудования", model=model)

    result = review_tier(
        title="Поставка оборудования для НК",
        rules_tier="L1",
        post_chat=post_chat,
    )
    assert result.tier == "L3"
    assert "Поставка" in result.reason_ru


@pytest.mark.unit
def test_review_tier_fallback_then_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROVOD_API_KEY", "test-key")
    calls: list[str] = []

    def post_chat(*, model: str, user_content: str) -> AiTierResult:
        calls.append(model)
        if model == "claude-sonnet-4-6":
            raise AiTierError("http_500")
        return AiTierResult(tier="L2", reason_ru="Услуга НК", model=model)

    result = review_tier(title="УЗК сварных", rules_tier="L2", post_chat=post_chat)
    assert result.tier == "L2"
    assert calls == ["claude-sonnet-4-6", "openai-gpt-5-4"]


@pytest.mark.unit
def test_review_tier_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROVOD_API_KEY", raising=False)
    with pytest.raises(AiTierError) as exc:
        review_tier(title="x", rules_tier="L1")
    assert "missing_api_key" in str(exc.value)

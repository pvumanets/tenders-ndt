"""Unit: provod.ai review_tier with mock post_chat (no network)."""
from __future__ import annotations

import pytest

from app.ai.provod import AiTierError, AiTierResult, build_user_prompt, review_tier


@pytest.mark.unit
def test_build_user_prompt_title_only() -> None:
    text = build_user_prompt(title="Поставка оборудования для НК")
    assert text == "title: Поставка оборудования для НК"
    assert "rules_tier" not in text
    assert "fit_reason" not in text


@pytest.mark.unit
def test_build_user_prompt_with_customer_and_description() -> None:
    text = build_user_prompt(
        title="УЗК сварных",
        customer_name="ООО Тест",
        description="x" * 900,
    )
    assert "title: УЗК сварных" in text
    assert "customer: ООО Тест" in text
    assert "description: " in text
    assert len(text.split("description: ", 1)[1]) == 800
    assert "rules_tier" not in text
    assert "fit_reason" not in text


@pytest.mark.unit
def test_build_user_prompt_skips_empty_optional() -> None:
    text = build_user_prompt(title="НК", customer_name="  ", description="")
    assert text == "title: НК"


@pytest.mark.unit
def test_review_tier_success_primary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROVOD_API_KEY", "test-key")
    captured: list[str] = []

    def post_chat(*, model: str, user_content: str) -> AiTierResult:
        captured.append(user_content)
        assert "title:" in user_content
        assert "rules_tier" not in user_content
        assert "fit_reason" not in user_content
        return AiTierResult(tier="L3", reason_ru="Поставка оборудования", model=model)

    result = review_tier(
        title="Поставка оборудования для неразрушающего контроля",
        post_chat=post_chat,
    )
    assert result.tier == "L3"
    assert "Поставка" in result.reason_ru
    assert captured and "Поставка оборудования для неразрушающего контроля" in captured[0]


@pytest.mark.unit
def test_review_tier_golden_hydrocracking_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROVOD_API_KEY", "test-key")
    title = (
        "Проведение неразрушающего контроля (НК) методом ультразвукового контроля "
        "и цветной дефектоскопии сварных соединений по объекту: Комплекс гидрокрекинга"
    )

    def post_chat(*, model: str, user_content: str) -> AiTierResult:
        assert user_content.startswith(f"title: {title}")
        assert "rules_tier" not in user_content
        return AiTierResult(tier="L1", reason_ru="Услуга УЗК на объекте нефтепереработки", model=model)

    result = review_tier(title=title, customer_name="ООО ОРГЭНЕРГОНЕФТЬ", post_chat=post_chat)
    assert result.tier == "L1"


@pytest.mark.unit
def test_review_tier_fallback_then_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROVOD_API_KEY", "test-key")
    calls: list[str] = []

    def post_chat(*, model: str, user_content: str) -> AiTierResult:
        calls.append(model)
        if model == "claude-sonnet-4-6":
            raise AiTierError("http_500")
        return AiTierResult(tier="L2", reason_ru="Услуга НК", model=model)

    result = review_tier(title="УЗК сварных", post_chat=post_chat)
    assert result.tier == "L2"
    assert calls == ["claude-sonnet-4-6", "openai-gpt-5-4"]


@pytest.mark.unit
def test_review_tier_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROVOD_API_KEY", raising=False)
    with pytest.raises(AiTierError) as exc:
        review_tier(title="x")
    assert "missing_api_key" in str(exc.value)

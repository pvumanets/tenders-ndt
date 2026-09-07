"""Unit: AI parse isolation + cap 100 (083). No network / DB."""
from __future__ import annotations

import json

import pytest

from app.ai.provod import AiTierError, AiTierResult, _parse_json_content, review_tier
from app.api.inbox import AI_REVIEW_CAP


@pytest.mark.unit
def test_parse_json_content_second_loads_becomes_ai_tier_error() -> None:
    with pytest.raises(AiTierError, match="invalid_json"):
        _parse_json_content("prefix {not-json { broken")
    with pytest.raises(AiTierError, match="invalid_json"):
        _parse_json_content("{")


@pytest.mark.unit
def test_parse_fail_does_not_abort_neighbor_ok() -> None:
    ok = _parse_json_content('{"tier":"L1","reason_ru":"Услуга НК на объекте"}')
    with pytest.raises(AiTierError):
        _parse_json_content("not json {broken")
    neighbor = _parse_json_content('{"tier":"L2","reason_ru":"Смешанный предмет"}')
    assert ok["tier"] == "L1"
    assert neighbor["tier"] == "L2"


@pytest.mark.unit
def test_review_batch_continues_after_parse_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROVOD_API_KEY", "test-key")
    monkeypatch.setenv("PROVOD_MODEL_CHAIN", "m1")
    results: list[str] = []

    def post_chat(*, model: str, user_content: str) -> AiTierResult:
        del model
        if "broken" in user_content:
            raise AiTierError("invalid_json") from json.JSONDecodeError("x", "x", 0)
        return AiTierResult(tier="L1", reason_ru="Услуга НК", model="m1")

    for title in ("ok lot", "broken json", "ok neighbor"):
        try:
            results.append(review_tier(title=title, post_chat=post_chat).tier)
        except AiTierError:
            results.append("fail")
    assert results == ["L1", "fail", "L1"]


@pytest.mark.unit
def test_ai_review_cap_is_100() -> None:
    assert AI_REVIEW_CAP == 100
    pairs = list(range(250))
    assert len(pairs[:AI_REVIEW_CAP]) == 100

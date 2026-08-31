"""Unit: LOCOR JSON → Netscape, cookie POST, TP list without jar, ops soft-fail."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import platforms as platforms_api
from app.api import runner
from app.api.main import app
from app.api.notify import notify_ops_session
from app.api.state import STATE
from app.mail import smtp as smtp_mod
from app.worker.cookies import (
    CookieConvertError,
    json_locor_to_netscape,
    parse_netscape_cookies,
    write_netscape_cookies,
)

_SECRET_VALUE = "qa055_secret_cookie_value_xyz"


def _client() -> TestClient:
    try:
        return TestClient(app, lifespan="off")
    except TypeError:
        return TestClient(app)


def _locor_items() -> list[dict[str, Any]]:
    return [
        {
            "domain": ".rostender.info",
            "name": "PHPSESSID",
            "value": _SECRET_VALUE,
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "expirationDate": 1893456000,
        }
    ]


def _assert_no_cookie_values(body: object) -> None:
    blob = json.dumps(body, ensure_ascii=False)
    assert _SECRET_VALUE not in blob
    assert "Netscape HTTP Cookie File" not in blob


@pytest.mark.unit
def test_json_locor_roundtrip(tmp_path: Path) -> None:
    text = json_locor_to_netscape(_locor_items())
    path = tmp_path / "cookies.rostender.txt"
    write_netscape_cookies(path, text)
    parsed = parse_netscape_cookies(path)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "PHPSESSID"
    assert parsed[0]["value"] == _SECRET_VALUE
    assert parsed[0]["domain"] in {".rostender.info", "rostender.info"}
    assert parsed[0]["secure"] is True


@pytest.mark.unit
def test_json_locor_rejects_bad() -> None:
    with pytest.raises(CookieConvertError, match="empty_cookies"):
        json_locor_to_netscape([])
    with pytest.raises(CookieConvertError, match="invalid_cookies_json"):
        json_locor_to_netscape({"not": "array"})
    with pytest.raises(CookieConvertError, match="invalid_cookies_json"):
        json_locor_to_netscape([{"domain": "", "name": "x", "value": "y"}])
    with pytest.raises(CookieConvertError, match="invalid_cookies_json"):
        json_locor_to_netscape([{"domain": "a.com", "name": "x", "value": ""}])
    with pytest.raises(CookieConvertError, match="invalid_cookies_json"):
        json_locor_to_netscape([{"domain": "a.com", "name": "x"}])


@pytest.mark.unit
def test_upload_cookies_401_and_404() -> None:
    with _client() as client:
        anon = client.post("/api/platforms/rostender/cookies", json=_locor_items())
        assert anon.status_code == 401
        _assert_no_cookie_values(anon.json())


@pytest.mark.unit
def test_upload_cookies_writes_and_probes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    jar = tmp_path / "cookies.rostender.txt"
    monkeypatch.setenv("ROSTENDER_COOKIES_FILE", str(jar))
    monkeypatch.setattr(
        platforms_api, "_probe_platform", lambda platform_id: "ok"
    )
    monkeypatch.setattr(
        platforms_api.notify, "notify_ops_session", lambda **_kw: "smtp_unconfigured"
    )

    result = platforms_api.upload_platform_cookies("rostender", _locor_items())
    assert result == {"platform_id": "rostender", "session": "ok", "probed": True}
    _assert_no_cookie_values(result)
    assert jar.is_file()
    assert _SECRET_VALUE in jar.read_text(encoding="utf-8")
    assert STATE.snapshot()["sessions"]["rostender"] == "ok"

    with pytest.raises(platforms_api.PlatformNotFound):
        platforms_api.upload_platform_cookies("b2b-center", _locor_items())
    with pytest.raises(platforms_api.CookieUploadError, match="empty_cookies"):
        platforms_api.upload_platform_cookies("rostender", [])
    with pytest.raises(platforms_api.CookieUploadError, match="invalid_cookies_json"):
        platforms_api.upload_platform_cookies("rostender", {"x": 1})


@pytest.mark.unit
def test_upload_bad_session_triggers_ops(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    jar = tmp_path / "cookies.roseltorg.txt"
    monkeypatch.setenv("ROSELTORG_COOKIES_FILE", str(jar))
    monkeypatch.setattr(platforms_api, "_probe_platform", lambda platform_id: "expired")
    calls: list[dict[str, str]] = []

    def _ops(**kwargs: str) -> str:
        calls.append(dict(kwargs))
        return "smtp_unconfigured"

    monkeypatch.setattr(platforms_api.notify, "notify_ops_session", _ops)
    result = platforms_api.upload_platform_cookies("roseltorg", _locor_items())
    assert result["session"] == "expired"
    assert result["probed"] is True
    _assert_no_cookie_values(result)
    assert calls == [{"platform_id": "roseltorg", "session": "expired"}]
    # Poll must not invent ok over expired while file exists.
    STATE.set_session("expired", platform_id="roseltorg")
    jar.write_text(json_locor_to_netscape(_locor_items()), encoding="utf-8")
    monkeypatch.setattr(runner.roseltorg_worker, "cookies_present", lambda: True)
    runner.refresh_session(probe_roseltorg_live=False)
    assert STATE.snapshot()["sessions"]["roseltorg"] == "expired"


@pytest.mark.unit
def test_ops_smtp_unconfigured(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("MAIL_OPS_TO", raising=False)
    with caplog.at_level("INFO"):
        status = notify_ops_session(platform_id="rostender", session="expired")
    assert status == "smtp_unconfigured"
    assert any("smtp_unconfigured" in r.message for r in caplog.records)
    assert smtp_mod.smtp_configured() is False


@pytest.mark.unit
def test_tender_pro_missing_jar_still_lists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    missing = tmp_path / "no-tp-cookies.txt"
    monkeypatch.setenv("TENDER_PRO_COOKIES_FILE", str(missing))
    monkeypatch.setattr(
        runner.tender_pro_worker,
        "probe_tender_pro_cookies",
        lambda *a, **k: "missing",
    )
    called: list[str] = []

    def fake_scrape(**_kwargs: Any) -> list[dict]:
        called.append("scrape")
        return [
            {
                "tender_id": "1227021",
                "title": "ВИК",
                "url": "https://www.tender.pro/api/tenders/1227021",
                "customer_name": "ООО",
                "deadline_msk": "01.01.2027",
                "status": "Приём заявок",
                "location": "",
                "nmck": None,
            }
        ]

    monkeypatch.setattr(runner.tender_pro_worker, "scrape_queries", fake_scrape)
    monkeypatch.setattr(
        runner.tender_pro_worker,
        "enrich_cards",
        lambda scored, card_ids, **_k: (scored, []),
    )
    monkeypatch.setattr(runner, "score_rows", lambda rows: (rows, {"L1": 1, "L2": 0, "L3": 0, "noise": 0}, ["1227021"]))
    monkeypatch.setattr(
        runner,
        "rescore_rows",
        lambda rows: (rows, {"L1": 1, "L2": 0, "L3": 0, "noise": 0}, ["1227021"]),
    )
    monkeypatch.setattr(runner, "write_artifacts", lambda *_a, **_k: None)
    monkeypatch.setattr(runner, "_ingest_step", lambda **_k: None)
    monkeypatch.setattr(runner, "_download_docs", lambda *_a, **_k: None)
    monkeypatch.setattr(runner, "download_docs_enabled", lambda: False)

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    status = runner._run_tender_pro(
        item={
            "name": "TP",
            "platform_id": "tender-pro",
            "queries": ["ВИК"],
            "exclude": [],
            "limit_n": 10,
        },
        run_dir=run_dir,
    )
    assert status == "done"
    assert called == ["scrape"]
    assert STATE.snapshot()["sessions"]["tender-pro"] == "missing_cookies"

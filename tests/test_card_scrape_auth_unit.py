"""Unit: card scrape AuthError path after 403 pass-through (R1 / 078)."""
from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.worker import card_scrape
from app.worker.list_scrape import AuthError


def _write_jar(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "# Netscape HTTP Cookie File",
                ".rostender.info\tTRUE\t/\tFALSE\t0\tPHPSESSID\tsecret",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


@pytest.mark.unit
def test_enrich_cards_five_403_raises_auth_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jar = _write_jar(tmp_path / "cookies.txt")
    rows = [
        {
            "tender_id": str(i),
            "title": f"t{i}",
            "url": f"https://rostender.info/tender/{i}",
            "tier": "L1",
        }
        for i in range(1, 6)
    ]

    def always_403(client, method, url, **kwargs):
        del client, method, kwargs
        request = httpx.Request("GET", url)
        return httpx.Response(403, request=request, text="Forbidden")

    monkeypatch.setattr(card_scrape, "request_allowlisted", always_403)

    with pytest.raises(AuthError, match="Too many 403"):
        card_scrape.enrich_cards(
            rows,
            [r["tender_id"] for r in rows],
            cookies_path=jar,
            delay_s=0,
        )

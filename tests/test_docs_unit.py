"""Unit: P5.5 docs parse, sanitize, DOWNLOAD_DOCS skip, mock download. No database."""
from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.api.inbox import InboxQueryError, download_document
from app.worker.card_scrape import parse_document_links
from app.worker.docs import (
    download_docs_enabled,
    download_inbox_docs,
    filename_from_content_disposition,
    sanitize_filename,
)

_CARD_HTML = """
<html><body>
  <h2>Документация</h2>
  <a href="/nav">Описание</a>
  <a href="/tender/45289101/download/111">ТЗ_УЗК.pdf</a>
  <span>420 КБ</span>
  <a href="/tender/45289101/download/222">Проект_договора.docx</a>
  <a href="/tender/45289101/download-archive">Скачать одним архивом</a>
</body></html>
"""

_ARCHIVE_ONLY_HTML = """
<html><body>
  <a href="/region/x/y/45289101-tender-foo">карточка</a>
  <a href="/tender/45289101/zip">Скачать одним архивом</a>
</body></html>
"""


@pytest.mark.unit
def test_sanitize_filename_strips_traversal() -> None:
    assert sanitize_filename("ТЗ_УЗК.pdf") == "ТЗ_УЗК.pdf"
    assert sanitize_filename("../etc/passwd") == "passwd"
    assert sanitize_filename("..") is None
    assert sanitize_filename("foo/bar.pdf") == "bar.pdf"
    assert sanitize_filename("a\\b\\c.xls") == "c.xls"
    assert sanitize_filename("") is None


@pytest.mark.unit
def test_filename_from_content_disposition() -> None:
    assert (
        filename_from_content_disposition('attachment; filename="TZ.pdf"', "x.bin")
        == "TZ.pdf"
    )
    assert (
        filename_from_content_disposition(
            "attachment; filename*=UTF-8''%D0%A2%D0%97.pdf",
            "x.bin",
        )
        == "ТЗ.pdf"
    )
    assert filename_from_content_disposition(None, "fallback.bin") == "fallback.bin"


@pytest.mark.unit
def test_parse_document_links_prefers_files_over_archive() -> None:
    links = parse_document_links(_CARD_HTML, "https://rostender.info/tender/45289101")
    names = [row["name"] for row in links]
    assert names == ["ТЗ_УЗК.pdf", "Проект_договора.docx"]
    assert all("/download/" in row["url"] for row in links)
    assert not any("архивом" in row["name"] for row in links)


@pytest.mark.unit
def test_parse_document_links_archive_fallback() -> None:
    links = parse_document_links(
        _ARCHIVE_ONLY_HTML, "https://rostender.info/region/x/y/45289101-tender-foo"
    )
    assert len(links) == 1
    assert links[0]["name"] == "docs.zip"
    assert links[0]["url"].endswith("/tender/45289101/zip")


@pytest.mark.unit
def test_download_document_rejects_traversal_before_db() -> None:
    with pytest.raises(InboxQueryError, match="invalid_filename"):
        download_document("45289101", "..")
    with pytest.raises(InboxQueryError, match="invalid_filename"):
        download_document("45289101", "../TZ.pdf")
    with pytest.raises(InboxQueryError, match="invalid_filename"):
        download_document("45289101", "foo/bar.pdf")


@pytest.mark.unit
def test_download_docs_disabled_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DOWNLOAD_DOCS", "0")
    assert download_docs_enabled() is False
    dest = tmp_path / "docs"
    called = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["n"] += 1
        return httpx.Response(200, content=b"%PDF")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = download_inbox_docs(
        [
            {
                "tender_id": "45289101",
                "score": 7,
                "doc_links": [{"name": "TZ.pdf", "url": "https://x/file"}],
            }
        ],
        cookies_path=tmp_path / "missing.txt",
        docs_root=dest,
        delay_s=0,
        persist_meta=False,
        client=client,
    )
    assert result.saved == 0
    assert called["n"] == 0
    assert not dest.exists()


@pytest.mark.unit
def test_download_docs_saves_score_ge_4_skips_l3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DOWNLOAD_DOCS", "1")
    dest = tmp_path / "docs"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"%PDF-fake",
            headers={
                "content-type": "application/pdf",
                "content-disposition": 'attachment; filename="TZ.pdf"',
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = download_inbox_docs(
        [
            {
                "tender_id": "rostender:45289101",
                "score": 7,
                "doc_links": [{"name": "TZ.pdf", "url": "https://x/download/1"}],
            },
            {
                "tender_id": "rostender:low",
                "score": 3,
                "doc_links": [{"name": "nope.pdf", "url": "https://x/download/2"}],
            },
        ],
        cookies_path=tmp_path / "missing.txt",
        docs_root=dest,
        delay_s=0,
        persist_meta=False,
        client=client,
    )
    assert result.saved == 1
    assert result.errors == 0
    saved = dest / "rostender__45289101" / "TZ.pdf"
    assert saved.is_file()
    assert saved.read_bytes() == b"%PDF-fake"
    assert not (dest / "rostender__low").exists()

    again = download_inbox_docs(
        [
            {
                "tender_id": "rostender:45289101",
                "score": 7,
                "doc_links": [{"name": "TZ.pdf", "url": "https://x/download/1"}],
            }
        ],
        cookies_path=tmp_path / "missing.txt",
        docs_root=dest,
        delay_s=0,
        persist_meta=False,
        client=client,
    )
    assert again.skipped == 1
    assert again.saved == 0

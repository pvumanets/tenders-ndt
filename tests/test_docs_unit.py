"""Unit: P5.5/094 docs parse, sanitize, zip download, DOWNLOAD_DOCS skip. No database."""
from __future__ import annotations

import zipfile
from pathlib import Path

import httpx
import pytest

from app.api.inbox import InboxQueryError, download_document
from app.db.models import LotState
from app.worker.card_scrape import parse_document_links
from app.worker.docs import (
    DOC_STATUS_EXTERNAL_ONLY,
    DOC_STATUS_PENDING_AI,
    DOC_STATUS_READY,
    DOC_STATUS_UNSUPPORTED,
    ZIP_FILENAME,
    download_docs_enabled,
    download_inbox_docs,
    download_lot_zip,
    filename_from_content_disposition,
    resolve_docs_status_for_api,
    sanitize_filename,
    split_doc_links,
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

_TENDER_FILES_HTML = """
<html><body>
  <footer><a href="/docs/api">Документация API</a></footer>
  <div class="tender-files">
    <div class="tender-files__item">
      <a class="tender-files__link" data-extension="rar" href="#"><span class="title">Документация.rar</span></a>
      <a class="tender-files__download" href="https://files.rostender.info/?t=abc123"></a>
    </div>
    <div class="tender-files__item">
      <a class="tender-files__link" href="#"><span class="title">ТЗ_УЗК.pdf</span></a>
      <a class="tender-files__download" href="https://files.rostender.info/?t=def456"></a>
    </div>
  </div>
  <a href="/docs/api">API</a>
</body></html>
"""

_DOCS_API_ONLY_HTML = """
<html><body>
  <a href="/nav">Описание</a>
  <a href="/docs/api">Документация API</a>
  <a href="https://rostender.info/docs/api">API</a>
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
def test_parse_document_links_tender_files_block() -> None:
    links = parse_document_links(
        _TENDER_FILES_HTML, "https://rostender.info/tender/45289101"
    )
    assert len(links) == 2
    assert links[0]["name"] == "Документация.rar"
    assert links[0]["url"] == "https://files.rostender.info/?t=abc123"
    assert links[1]["name"] == "ТЗ_УЗК.pdf"
    assert links[1]["url"] == "https://files.rostender.info/?t=def456"
    assert not any("/docs/api" in row["url"] for row in links)


@pytest.mark.unit
def test_parse_document_links_ignores_site_docs_api() -> None:
    links = parse_document_links(
        _DOCS_API_ONLY_HTML, "https://rostender.info/tender/45289101"
    )
    assert links == []


@pytest.mark.unit
def test_download_document_rejects_traversal_before_db() -> None:
    with pytest.raises(InboxQueryError, match="invalid_filename"):
        download_document("45289101", "..")
    with pytest.raises(InboxQueryError, match="invalid_filename"):
        download_document("45289101", "../TZ.pdf")
    with pytest.raises(InboxQueryError, match="invalid_filename"):
        download_document("45289101", "foo/bar.pdf")


@pytest.mark.unit
def test_split_doc_links_allowlist() -> None:
    allowed, external = split_doc_links(
        [
            {"name": "a.pdf", "url": "https://rostender.info/a.pdf"},
            {"name": "b.pdf", "url": "https://evil.example/b.pdf"},
        ]
    )
    assert len(allowed) == 1
    assert allowed[0]["name"] == "a.pdf"
    assert len(external) == 1


@pytest.mark.unit
def test_resolve_docs_status_pending_ai() -> None:
    assert resolve_docs_status_for_api(None, ai_reviewed=False) == DOC_STATUS_PENDING_AI
    state = LotState(tender_id="x", docs_status=DOC_STATUS_READY)
    assert resolve_docs_status_for_api(state, ai_reviewed=True) == DOC_STATUS_READY


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
                "tier": "L1",
                "doc_links": [{"name": "TZ.pdf", "url": "https://rostender.info/file"}],
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
def test_download_lot_zip_external_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOWNLOAD_DOCS", "1")
    status = download_lot_zip(
        tender_id="rostender:1",
        links=[{"name": "x.pdf", "url": "https://tektorg.ru/file.pdf"}],
        platform_id="rostender",
        lot_url="https://rostender.info/tender/1",
        cookies_path=tmp_path / "c.txt",
        docs_root=tmp_path / "docs",
        persist_meta=False,
    )
    assert status == DOC_STATUS_EXTERNAL_ONLY


@pytest.mark.unit
def test_download_lot_zip_unsupported(tmp_path: Path) -> None:
    status = download_lot_zip(
        tender_id="oilb2bcs:1",
        links=[{"name": "x.pdf", "url": "https://oilb2bcs.ru/x.pdf"}],
        platform_id="oilb2bcs",
        lot_url=None,
        cookies_path=tmp_path / "c.txt",
        docs_root=tmp_path / "docs",
        persist_meta=False,
    )
    assert status == DOC_STATUS_UNSUPPORTED


@pytest.mark.unit
def test_download_docs_saves_zip_for_l1(
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
                "tier": "L1",
                "doc_links": [{"name": "TZ.pdf", "url": "https://rostender.info/download/1"}],
            },
            {
                "tender_id": "rostender:low",
                "score": 3,
                "tier": "noise",
                "doc_links": [{"name": "nope.pdf", "url": "https://rostender.info/download/2"}],
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
    saved = dest / "rostender__45289101" / ZIP_FILENAME
    assert saved.is_file()
    with zipfile.ZipFile(saved) as zf:
        names = zf.namelist()
        assert "TZ.pdf" in names
        assert zf.read("TZ.pdf") == b"%PDF-fake"
    assert not (dest / "rostender__low").exists()

    again = download_inbox_docs(
        [
            {
                "tender_id": "rostender:45289101",
                "score": 7,
                "tier": "L1",
                "doc_links": [{"name": "TZ.pdf", "url": "https://rostender.info/download/1"}],
            }
        ],
        cookies_path=tmp_path / "missing.txt",
        docs_root=dest,
        delay_s=0,
        persist_meta=False,
        client=client,
    )
    assert again.saved == 1  # status ready; counted as saved in legacy helper
    assert DOC_STATUS_READY in again.by_status


@pytest.mark.unit
def test_execute_docs_pass_ignores_sticky_queue_stop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.inbox import execute_docs_pass
    from app.api.state import STATE
    from app.worker.docs import DocsPassResult

    STATE.request_stop()
    assert STATE.should_stop() is True
    captured: dict = {}

    def fake_run(ids, **kwargs):  # noqa: ANN001
        captured["ids"] = list(ids)
        captured["kwargs"] = kwargs
        return DocsPassResult()

    monkeypatch.setenv("DOWNLOAD_DOCS", "1")
    monkeypatch.setattr("app.worker.docs.download_docs_enabled", lambda: True)
    monkeypatch.setattr("app.worker.docs.run_docs_pass", fake_run)
    monkeypatch.setattr("app.worker.docs.finalize_docs_status_for_ids", lambda *a, **k: 0)

    out = execute_docs_pass(["rostender:1", "rostender:2"])
    assert captured["ids"] == ["rostender:1", "rostender:2"]
    assert captured["kwargs"].get("should_stop") is None
    assert out["ids"] == 2
    STATE.stop_requested = False


@pytest.mark.unit
def test_run_docs_pass_request_rejects_bad_body() -> None:
    from app.api.inbox import InboxQueryError, run_docs_pass_request

    with pytest.raises(InboxQueryError, match="invalid_body"):
        run_docs_pass_request({"tender_ids": "nope"})
    with pytest.raises(InboxQueryError, match="invalid_body"):
        run_docs_pass_request({"tender_ids": []})


@pytest.mark.unit
def test_download_lot_zip_disabled_persists_pending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DOWNLOAD_DOCS", "0")
    called: list[str] = []

    def fake_set(tender_id: str, *, status: str, external_url: str | None = None) -> None:
        called.append(status)

    monkeypatch.setattr("app.worker.docs._set_lot_docs_state", fake_set)
    status = download_lot_zip(
        tender_id="rostender:1",
        links=[{"name": "a.pdf", "url": "https://rostender.info/a.pdf"}],
        platform_id="rostender",
        lot_url="https://rostender.info/tender/1",
        cookies_path=tmp_path / "c.txt",
        docs_root=tmp_path / "docs",
        persist_meta=True,
    )
    from app.worker.docs import DOC_STATUS_PENDING_DOWNLOAD

    assert status == DOC_STATUS_PENDING_DOWNLOAD
    assert called == [DOC_STATUS_PENDING_DOWNLOAD]

"""Unit: per-step run artifacts + results steps list (085)."""
from __future__ import annotations

import json

import pytest

from app.api import results, runner
from app.api.state import STATE


@pytest.mark.unit
def test_artifact_step_dirs_do_not_overwrite(tmp_path) -> None:
    day = tmp_path / "2026-09-07"
    day.mkdir()
    item = {"name": "НК", "group_name": "методы", "platform_id": "rostender"}
    first = runner._artifact_step_dir(day, item, 0)
    second = runner._artifact_step_dir(day, item, 1)
    again = runner._artifact_step_dir(day, item, 0)
    assert first != second
    assert again != first
    assert first.is_dir() and second.is_dir() and again.is_dir()
    (first / "scored-list.json").write_text("[]", encoding="utf-8")
    (second / "scored-list.json").write_text("[]", encoding="utf-8")
    assert (first / "scored-list.json").is_file()
    assert (second / "scored-list.json").is_file()


@pytest.mark.unit
def test_list_results_exposes_two_steps(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(results, "_runs_root", lambda: tmp_path)
    day = tmp_path / "2026-09-07"
    step_a = day / "00_metody_rostender"
    step_b = day / "01_metody_tender-pro"
    for path, tid in ((step_a, "a"), (step_b, "b")):
        path.mkdir(parents=True)
        (path / "scored-list.json").write_text(
            json.dumps(
                [
                    {
                        "tender_id": tid,
                        "tier": "L1",
                        "title": tid,
                        "rank": 1,
                        "score": 8,
                    }
                ]
            ),
            encoding="utf-8",
        )
    prev = STATE.run_dir
    STATE.set_run_dir(str(day))
    try:
        out = results.list_results()
    finally:
        if prev:
            STATE.set_run_dir(prev)
        else:
            STATE.run_dir = None
    assert len(out["steps"]) == 2
    ids = {row["step_id"] for row in out["steps"]}
    assert "00_metody_rostender" in ids
    assert "01_metody_tender-pro" in ids
    assert out["run_dir"]
    assert out["total"] >= 1

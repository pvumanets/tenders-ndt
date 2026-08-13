"""Unit: VPS deploy aborts on dirty tree; secrets/runs untracked are ok."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_BOOTSTRAP = Path(__file__).resolve().parents[1] / "scripts" / "vps-bootstrap.py"
_SPEC = importlib.util.spec_from_file_location("vps_bootstrap", _BOOTSTRAP)
assert _SPEC is not None and _SPEC.loader is not None
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


@pytest.mark.unit
def test_clean_tree_allows_reset() -> None:
    assert _MOD.deploy_blocked_reason("") is None
    assert _MOD.deploy_blocked_reason("\n") is None


@pytest.mark.unit
def test_tracked_modify_blocks() -> None:
    reason = _MOD.deploy_blocked_reason(" M app/web/src/App.tsx")
    assert reason is not None
    assert "App.tsx" in reason
    assert "abort reset" in reason


@pytest.mark.unit
def test_staged_and_rename_block() -> None:
    staged = _MOD.deploy_blocked_reason("M  app/web/src/components/scout/TechRunPanel.tsx")
    assert staged is not None
    assert "TechRunPanel.tsx" in staged
    renamed = _MOD.deploy_blocked_reason("R  app/web/src/copy.ts -> app/web/src/copy-ru.ts")
    assert renamed is not None
    assert "copy-ru.ts" in renamed


@pytest.mark.unit
def test_untracked_secrets_allow() -> None:
    porcelain = "\n".join(
        [
            "?? .env",
            "?? cookies.rostender.txt",
            "?? cookies.sibur.txt",
        ]
    )
    assert _MOD.deploy_blocked_reason(porcelain) is None


@pytest.mark.unit
def test_untracked_runs_allow_untracked_app_blocks() -> None:
    mixed = "\n".join(
        [
            "?? runs/2026-08-13/notes.md",
            "?? app/web/src/App.tsx",
        ]
    )
    reason = _MOD.deploy_blocked_reason(mixed)
    assert reason is not None
    assert "App.tsx" in reason
    assert "runs/2026-08-13" not in reason


@pytest.mark.unit
def test_only_untracked_runs_allows() -> None:
    assert _MOD.deploy_blocked_reason("?? runs/2026-08-13/notes.md") is None

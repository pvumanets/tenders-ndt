#!/usr/bin/env python3
"""Build tenders-ndt-runtime:latest only when requirements.txt hash changes.

No secrets. Exit 0 on cache hit or successful rebuild.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"
DOCKERFILE = ROOT / "Dockerfile.runtime"
IMAGE = os.environ.get("SCOUT_RUNTIME_IMAGE", "tenders-ndt-runtime:latest")
LABEL_KEY = "scout.requirements_sha"


def _sha12() -> str:
    data = REQUIREMENTS.read_bytes()
    return hashlib.sha256(data).hexdigest()[:12]


def _image_label() -> str | None:
    proc = subprocess.run(
        [
            "docker",
            "image",
            "inspect",
            IMAGE,
            "--format",
            '{{index .Config.Labels "scout.requirements_sha"}}',
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    value = (proc.stdout or "").strip()
    return value or None


def main() -> int:
    if not REQUIREMENTS.is_file():
        print(f"ensure-runtime: missing {REQUIREMENTS}", file=sys.stderr)
        return 1
    if not DOCKERFILE.is_file():
        print(f"ensure-runtime: missing {DOCKERFILE}", file=sys.stderr)
        return 1

    want = _sha12()
    have = _image_label()
    if have == want:
        print(f"runtime: cached ({IMAGE} sha={want})")
        return 0

    reason = "missing" if have is None else f"sha {have} -> {want}"
    print(f"runtime: building {IMAGE} ({reason})")
    env = os.environ.copy()
    env["DOCKER_BUILDKIT"] = "1"
    cmd = [
        "docker",
        "build",
        "-f",
        str(DOCKERFILE),
        "--label",
        f"{LABEL_KEY}={want}",
        "-t",
        IMAGE,
        str(ROOT),
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env, check=False)
    if proc.returncode != 0:
        print("ensure-runtime: docker build failed", file=sys.stderr)
        return proc.returncode
    print(f"runtime: ready ({IMAGE} sha={want})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

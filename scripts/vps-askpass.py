"""SSH_ASKPASS helper: prints SCOUT_VPS_PASSWORD from .env.vps to stdout only."""

from pathlib import Path

env = Path(__file__).resolve().parents[1] / ".env.vps"
for line in env.read_text(encoding="utf-8").splitlines():
    if line.startswith("SCOUT_VPS_PASSWORD="):
        print(line.split("=", 1)[1].strip(), end="")
        break

#!/bin/sh
set -eu
alembic upgrade head
exec python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8765

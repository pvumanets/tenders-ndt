"""Smoke: prefixed rostender tender_id keeps viewed/manual_tier (024 intent)."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Lot, LotState, Run
from app.worker.platform_ids import compose_tender_id, volume_dir_name
from tests.conftest import SMOKE_PREFIX


@pytest.mark.smoke
def test_prefixed_tender_id_preserves_lot_state(smoke_db: sessionmaker[Session]) -> None:
    suffix = uuid4().hex[:8]
    native = f"9{int(suffix[:7], 16)}"[:12]
    if not native.isdigit():
        native = "998877665544"
    prefixed = compose_tender_id("rostender", native)
    query = f"{SMOKE_PREFIX}prefix_{suffix}"
    try:
        with smoke_db() as session:
            session.add(Run(query=query, status="done", limit_n=1))
            session.flush()
            run = session.query(Run).filter(Run.query == query).one()
            session.add(
                Lot(
                    tender_id=native,
                    run_id=run.id,
                    title="УЗК prefix smoke",
                    url=f"https://rostender.info/tender/{native}",
                    score=7,
                    tier="L1",
                    source_platform_id="rostender",
                    ingested_at=datetime.now(timezone.utc),
                )
            )
            session.add(LotState(tender_id=native, viewed=True, manual_tier="L2"))
            session.commit()

        with smoke_db() as session:
            old = session.get(Lot, native)
            assert old is not None
            state = session.get(LotState, native)
            assert state is not None
            viewed, manual = state.viewed, state.manual_tier
            session.delete(state)
            session.flush()
            session.add(
                Lot(
                    tender_id=prefixed,
                    run_id=old.run_id,
                    title=old.title,
                    url=old.url,
                    score=old.score,
                    tier=old.tier,
                    source_platform_id=old.source_platform_id,
                    ingested_at=old.ingested_at,
                )
            )
            session.delete(old)
            session.flush()
            session.add(LotState(tender_id=prefixed, viewed=viewed, manual_tier=manual))
            session.commit()

        with smoke_db() as session:
            lot = session.get(Lot, prefixed)
            state = session.get(LotState, prefixed)
            assert lot is not None
            assert state is not None
            assert state.viewed is True
            assert state.manual_tier == "L2"
            assert session.get(Lot, native) is None
            assert volume_dir_name(prefixed) == f"rostender__{native}"
    finally:
        with smoke_db() as session:
            for tid in (prefixed, native):
                row = session.get(LotState, tid)
                if row is not None:
                    session.delete(row)
                lot = session.get(Lot, tid)
                if lot is not None:
                    session.delete(lot)
            run = session.query(Run).filter(Run.query == query).one_or_none()
            if run is not None:
                session.delete(run)
            session.commit()

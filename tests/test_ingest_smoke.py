"""Smoke: P5.3 + P9 ingest insert / update-on-diff / skip; preserves lot_state."""
from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Lot, LotState, Run
from app.worker.ingest import ingest_run
from tests.conftest import SMOKE_PREFIX


def _row(tender_id: str, **overrides: object) -> dict:
    base: dict = {
        "tender_id": tender_id,
        "title": "УЗК сварных соединений (smoke)",
        "url": f"https://rostender.info/tender/{tender_id}",
        "score": 7,
        "tier": "L1",
        "location": "Казань",
        "customer_name": "ООО Smoke",
        "fit_reason": "услуга НК",
        "source_etp": "ТЭК-Торг",
        "deadline_msk": "2030-01-15",
        "price_rub": "100000",
    }
    base.update(overrides)
    return base


@pytest.mark.smoke
def test_ingest_upserts_score_ge_4_and_preserves_lot_state(
    smoke_db: sessionmaker[Session],
) -> None:
    suffix = uuid4().hex[:12]
    tender_id = f"rostender:{SMOKE_PREFIX}{suffix}"
    l3_id = f"rostender:{SMOKE_PREFIX}l3_{suffix}"
    query = f"{SMOKE_PREFIX}ingest_{suffix}"
    try:
        first = ingest_run(
            query=query,
            limit_n=10,
            status="done",
            rows=[
                _row(tender_id),
                _row(l3_id, score=3, tier="L3", title="авто-L3"),
            ],
        )
        assert first is not None
        assert first.lot_count == 1
        assert first.new_count == 1
        assert first.already_count == 0
        assert first.updated_count == 0
        with smoke_db() as session:
            lot = session.get(Lot, tender_id)
            assert lot is not None
            assert lot.score == 7
            assert lot.source_platform_id == "rostender"
            assert lot.location == "Казань"
            assert lot.url.endswith(tender_id)
            assert lot.ingested_at is not None
            assert session.get(Lot, l3_id) is None
            session.add(
                LotState(tender_id=tender_id, viewed=True, manual_tier="L2")
            )
            session.commit()

        same = ingest_run(
            query=query,
            limit_n=10,
            status="done",
            rows=[_row(tender_id)],
        )
        assert same is not None
        assert same.new_count == 0
        assert same.already_count == 1
        assert same.updated_count == 0

        second = ingest_run(
            query=query,
            limit_n=10,
            status="done",
            rows=[_row(tender_id, title="УЗК обновлён", score=8, deadline_msk="2030-02-01")],
        )
        assert second is not None
        assert second.new_count == 0
        assert second.already_count == 0
        assert second.updated_count == 1
        with smoke_db() as session:
            lot = session.get(Lot, tender_id)
            assert lot is not None
            assert lot.title == "УЗК обновлён"
            assert lot.score == 8
            assert lot.deadline_msk == "2030-02-01"
            assert lot.run_id == second.run_id
            n_lots = session.scalar(
                select(func.count()).select_from(Lot).where(Lot.tender_id == tender_id)
            )
            assert n_lots == 1
            state = session.get(LotState, tender_id)
            assert state is not None
            assert state.viewed is True
            assert state.manual_tier == "L2"
            n_runs = session.scalar(
                select(func.count()).select_from(Run).where(Run.query == query)
            )
            assert n_runs == 3
    finally:
        with smoke_db() as session:
            session.execute(delete(LotState).where(LotState.tender_id == tender_id))
            session.execute(delete(Lot).where(Lot.tender_id.in_((tender_id, l3_id))))
            session.execute(delete(Run).where(Run.query == query))
            session.commit()

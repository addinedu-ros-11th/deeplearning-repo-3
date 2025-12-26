from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import (
    Store, Device, DeviceType,
    TraySession, TraySessionStatus,
    RecognitionRun, DecisionState,
    Review, ReviewStatus
)
from app.schemas.ingest import TrayResultIngestRequest, TrayResultIngestResponse

router = APIRouter(dependencies=[Depends(require_admin_key)])

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

@router.post("/ingest/tray-result", response_model=TrayResultIngestResponse)
def ingest_tray_result(body: TrayResultIngestRequest, db: Session = Depends(get_db)):
    # 1) store/device resolve
    st = db.query(Store).filter(Store.store_code == body.store_code).first()
    if not st:
        raise HTTPException(status_code=404, detail="store not found")

    dv = (
        db.query(Device)
        .filter(Device.store_id == st.store_id)
        .filter(Device.device_code == body.device_code)
        .filter(Device.device_type == DeviceType.CHECKOUT)
        .first()
    )
    if not dv:
        raise HTTPException(status_code=404, detail="checkout device not found")

    # 2) tray_session upsert
    s = db.query(TraySession).filter(TraySession.session_uuid == body.session_uuid).first()
    if not s:
        s = TraySession(
            session_uuid=body.session_uuid,
            store_id=st.store_id,
            checkout_device_id=dv.device_id,
            status=TraySessionStatus.ACTIVE,
            attempt_limit=3,
            started_at=utcnow(),
            ended_at=None,
            end_reason=None,
            created_at=utcnow(),
        )
        db.add(s)
        db.commit()
        db.refresh(s)

    if body.attempt_no > s.attempt_limit:
        raise HTTPException(status_code=400, detail="attempt limit exceeded")

    # 3) recognition_run 중복 방지
    exists = (
        db.query(RecognitionRun)
        .filter(RecognitionRun.session_id == s.session_id, RecognitionRun.attempt_no == body.attempt_no)
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="run already exists for this attempt_no")

    # 4) decision enum validate
    if body.decision not in ("AUTO", "REVIEW", "UNKNOWN"):
        raise HTTPException(status_code=400, detail="invalid decision")

    run = RecognitionRun(
        session_id=s.session_id,
        attempt_no=body.attempt_no,
        overlap_score=body.overlap_score,
        decision=DecisionState(body.decision),
        result_json=body.result_json,
        created_at=utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    created_review_id = None
    if body.decision in ("REVIEW", "UNKNOWN"):
        open_review = (
            db.query(Review)
            .filter(Review.session_id == s.session_id, Review.status == ReviewStatus.OPEN)
            .first()
        )
        if not open_review:
            r = Review(
                session_id=s.session_id,
                run_id=run.run_id,
                status=ReviewStatus.OPEN,
                reason=body.decision,
                top_k_json=(body.result_json.get("top_k") if isinstance(body.result_json, dict) else None),
                confirmed_items_json=None,
                created_at=utcnow(),
            )
            db.add(r)
            db.commit()
            db.refresh(r)
            created_review_id = r.review_id

    return TrayResultIngestResponse(session_id=s.session_id, run_id=run.run_id, created_review_id=created_review_id)

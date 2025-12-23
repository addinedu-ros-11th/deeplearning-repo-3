from datetime import datetime, timezone
import uuid
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
from app.schemas.tray import TraySessionCreate, TraySessionOut, RecognitionRunCreate, RecognitionRunOut

router = APIRouter(dependencies=[Depends(require_admin_key)])

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

@router.post("/stores/{store_code}/checkouts/{device_code}/tray-sessions", response_model=TraySessionOut)
def create_tray_session(store_code: str, device_code: str, body: TraySessionCreate, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    device = (
        db.query(Device)
        .filter(Device.store_id == store.store_id, Device.device_code == device_code, Device.device_type == DeviceType.CHECKOUT)
        .first()
    )
    if not device:
        raise HTTPException(status_code=404, detail="checkout device not found")

    session_uuid = body.session_uuid or str(uuid.uuid4())
    exists = db.query(TraySession).filter(TraySession.session_uuid == session_uuid).first()
    if exists:
        raise HTTPException(status_code=409, detail="session_uuid already exists")

    s = TraySession(
        session_uuid=session_uuid,
        store_id=store.store_id,
        checkout_device_id=device.device_id,
        status=TraySessionStatus.ACTIVE,
        attempt_limit=body.attempt_limit,
        started_at=utcnow(),
        created_at=utcnow(),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@router.get("/tray-sessions/{session_uuid}", response_model=TraySessionOut)
def get_tray_session(session_uuid: str, db: Session = Depends(get_db)):
    s = db.query(TraySession).filter(TraySession.session_uuid == session_uuid).first()
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    return s

@router.post("/tray-sessions/{session_uuid}/recognition-runs", response_model=RecognitionRunOut)
def create_recognition_run(session_uuid: str, body: RecognitionRunCreate, db: Session = Depends(get_db)):
    s = db.query(TraySession).filter(TraySession.session_uuid == session_uuid).first()
    if not s:
        raise HTTPException(status_code=404, detail="session not found")

    if body.attempt_no < 1 or body.attempt_no > s.attempt_limit:
        raise HTTPException(status_code=400, detail="attempt_no out of range")

    exists = db.query(RecognitionRun).filter(RecognitionRun.session_id == s.session_id, RecognitionRun.attempt_no == body.attempt_no).first()
    if exists:
        raise HTTPException(status_code=409, detail="attempt already exists")

    run = RecognitionRun(
        session_id=s.session_id,
        attempt_no=body.attempt_no,
        overlap_score=body.overlap_score,
        decision=body.decision,
        result_json=body.result_json,
        created_at=utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    if body.decision in (DecisionState.REVIEW, DecisionState.UNKNOWN):
        open_review = db.query(Review).filter(Review.session_id == s.session_id, Review.status == ReviewStatus.OPEN).first()
        if not open_review:
            r = Review(
                session_id=s.session_id,
                run_id=run.run_id,
                status=ReviewStatus.OPEN,
                reason=body.decision.value,
                top_k_json=None,
                created_at=utcnow(),
            )
            db.add(r)
            db.commit()

    return run

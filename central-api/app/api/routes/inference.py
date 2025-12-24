from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import TraySession, RecognitionRun, DecisionState, Review, ReviewStatus, Store, Device, CctvEvent, CctvEventClip, CctvEventType, CctvEventStatus, DeviceType
from app.schemas.inference import InferTrayRequest, InferTrayResponse, CctvInferRequest, CctvInferResponse
from app.services.ai_client import AIClient, AIClientError
from sqlalchemy import text
from app.db.models import (
    TraySessionStatus, OrderHdr, OrderLine, OrderStatus, MenuItem
)

router = APIRouter(dependencies=[Depends(require_admin_key)])

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

TRAY_TIMEOUT_SEC = 30
OVERLAP_BLOCK_THRESHOLD_DEFAULT = 0.25

def _set_enum_or_str(obj, field: str, enum_value):
    # 컬럼이 Enum 타입이든 str 타입이든 모두 안전하게 할당
    try:
        setattr(obj, field, enum_value)
    except Exception:
        setattr(obj, field, getattr(enum_value, "value", str(enum_value)))

def _get_overlap_threshold_for_session(db: Session, s: TraySession) -> float:
    try:
        dv = db.query(Device).filter(Device.device_id == s.checkout_device_id).first()
        cfg = (dv.config_json or {}) if dv else {}
        gating = cfg.get("gating") or {}
        v = gating.get("overlap_block_threshold")
        if v is None:
            return OVERLAP_BLOCK_THRESHOLD_DEFAULT
        return float(v)
    except Exception:
        return OVERLAP_BLOCK_THRESHOLD_DEFAULT

@router.post("/tray-sessions/{session_uuid}/infer", response_model=InferTrayResponse)
def infer_tray(session_uuid: str, body: InferTrayRequest, db: Session = Depends(get_db)):
    s = db.query(TraySession).filter(TraySession.session_uuid == session_uuid).first()
    if not s:
        raise HTTPException(status_code=404, detail="session not found")

    last = (
        db.query(RecognitionRun)
        .filter(RecognitionRun.session_id == s.session_id)
        .order_by(RecognitionRun.attempt_no.desc())
        .first()
    )
    attempt_no = 1 if not last else (last.attempt_no + 1)
    if attempt_no > s.attempt_limit:
        raise HTTPException(status_code=400, detail="attempt limit exceeded")

    payload = body.model_dump()
    payload["session_uuid"] = session_uuid

    try:
        ai = AIClient()
        ai_resp = ai.infer_tray(payload, timeout_s=10.0)
    except AIClientError as e:
        raise HTTPException(status_code=502, detail=str(e))

    decision = ai_resp.get("decision")
    if decision not in ("AUTO", "REVIEW", "UNKNOWN"):
        raise HTTPException(status_code=502, detail="invalid decision from AI")

    run = RecognitionRun(
        session_id=s.session_id,
        attempt_no=attempt_no,
        overlap_score=ai_resp.get("overlap_score"),
        decision=DecisionState(decision),
        result_json=ai_resp.get("result_json", {}),
        created_at=utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    if decision in ("REVIEW", "UNKNOWN"):
        open_review = db.query(Review).filter(Review.session_id == s.session_id, Review.status == ReviewStatus.OPEN).first()
        if not open_review:
            r = Review(
                session_id=s.session_id,
                run_id=run.run_id,
                status=ReviewStatus.OPEN,
                reason=decision,
                top_k_json=ai_resp.get("result_json", {}).get("top_k"),
                confirmed_items_json=None,
                created_at=utcnow(),
            )
            db.add(r)
            db.commit()

    return InferTrayResponse(
        overlap_score=ai_resp.get("overlap_score"),
        decision=decision,
        result_json=ai_resp.get("result_json", {}),
    )

@router.post("/cctv/infer", response_model=CctvInferResponse)
def infer_cctv(body: CctvInferRequest, db: Session = Depends(get_db)):
    # store/device lookup by code (safer for external caller)
    if not body.store_code or not body.device_code:
        raise HTTPException(status_code=400, detail="store_code and device_code required")

    st = db.query(Store).filter(Store.store_code == body.store_code).first()
    if not st:
        raise HTTPException(status_code=404, detail="store not found")

    dv = (
        db.query(Device)
        .filter(Device.store_id == st.store_id)
        .filter(Device.device_code == body.device_code)
        .filter(Device.device_type == DeviceType.CCTV)
        .first()
    )
    if not dv:
        raise HTTPException(status_code=404, detail="cctv device not found")

    payload = body.model_dump()

    try:
        ai = AIClient()
        ai_resp = ai.infer_cctv(payload, timeout_s=20.0)
    except AIClientError as e:
        raise HTTPException(status_code=502, detail=str(e))

    events = ai_resp.get("events") or []
    created = []

    for ev in events:
        et = ev.get("event_type")
        conf = ev.get("confidence", 0.0)
        started = ev.get("started_at")
        ended = ev.get("ended_at")
        meta = ev.get("meta_json") or ev.get("meta") or {}

        if et not in ("VANDALISM", "VIOLENCE", "FALL", "WHEELCHAIR"):
            # ignore unknown event types (demo-safe)
            continue

        try:
            started_dt = datetime.fromisoformat(str(started).replace("Z", "").replace("T", " "))
            ended_dt = datetime.fromisoformat(str(ended).replace("Z", "").replace("T", " "))
        except Exception:
            # if parsing fails, skip
            continue

        row = CctvEvent(
            store_id=st.store_id,
            cctv_device_id=dv.device_id,
            event_type=CctvEventType(et),
            confidence=conf,
            status=CctvEventStatus.OPEN,
            started_at=started_dt,
            ended_at=ended_dt,
            meta_json=meta,
            created_at=utcnow(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)

        # optional clip row if request had a clip uri
        if body.clip_gcs_uri:
            clip = CctvEventClip(
                event_id=row.event_id,
                clip_gcs_uri=body.clip_gcs_uri,
                clip_start_at=(started_dt - timedelta(seconds=3)),
                clip_end_at=(ended_dt + timedelta(seconds=5)),
                created_at=utcnow(),
            )
            db.add(clip)
            db.commit()

        created.append({"event_id": row.event_id, "event_type": et})

    return CctvInferResponse(events=events)

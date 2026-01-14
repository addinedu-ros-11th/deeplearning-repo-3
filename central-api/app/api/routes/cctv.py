from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import Store, Device, DeviceType, CctvEvent, CctvEventClip
from app.schemas.cctv import CctvEventCreate, CctvEventOut, CctvEventClipOut
from app.services.gcs import generate_signed_url

router = APIRouter(dependencies=[Depends(require_admin_key)])

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def add_signed_urls_to_event(event: CctvEvent) -> dict:
    """CctvEvent를 dict로 변환하고 각 클립에 서명된 URL 추가"""
    event_dict = {
        "event_id": event.event_id,
        "store_id": event.store_id,
        "cctv_device_id": event.cctv_device_id,
        "event_type": event.event_type,
        "confidence": event.confidence,
        "status": event.status,
        "started_at": event.started_at,
        "ended_at": event.ended_at,
        "meta_json": event.meta_json,
        "created_at": event.created_at,
        "clips": [],
    }
    for clip in event.clips:
        clip_dict = {
            "clip_id": clip.clip_id,
            "event_id": clip.event_id,
            "clip_gcs_uri": clip.clip_gcs_uri,
            "clip_signed_url": generate_signed_url(clip.clip_gcs_uri, expiration_minutes=60),
            "clip_start_at": clip.clip_start_at,
            "clip_end_at": clip.clip_end_at,
            "created_at": clip.created_at,
        }
        event_dict["clips"].append(clip_dict)
    return event_dict

@router.post("/stores/{store_code}/cctv/{device_code}/events", response_model=CctvEventOut)
def create_cctv_event(store_code: str, device_code: str, body: CctvEventCreate, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    device = (
        db.query(Device)
        .filter(Device.store_id == store.store_id, Device.device_code == device_code, Device.device_type == DeviceType.CCTV)
        .first()
    )
    if not device:
        raise HTTPException(status_code=404, detail="cctv device not found")

    ev = CctvEvent(
        store_id=store.store_id,
        cctv_device_id=device.device_id,
        event_type=body.event_type,
        confidence=body.confidence,
        status=body.status,
        started_at=body.started_at.replace(tzinfo=None),
        ended_at=body.ended_at.replace(tzinfo=None),
        meta_json=body.meta_json,
        created_at=utcnow(),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    clip = CctvEventClip(
        event_id=ev.event_id,
        clip_gcs_uri=body.clip.clip_gcs_uri,
        clip_start_at=body.clip.clip_start_at.replace(tzinfo=None),
        clip_end_at=body.clip.clip_end_at.replace(tzinfo=None),
        created_at=utcnow(),
    )
    db.add(clip)
    db.commit()

    ev2 = db.query(CctvEvent).options(joinedload(CctvEvent.clips)).filter(CctvEvent.event_id == ev.event_id).first()
    return add_signed_urls_to_event(ev2)

@router.get("/cctv/events", response_model=list[CctvEventOut])
def list_cctv_events(
    store_id: int | None = None,
    device_id: int | None = None,
    from_: datetime | None = None,
    to: datetime | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(CctvEvent).options(joinedload(CctvEvent.clips))
    if store_id:
        q = q.filter(CctvEvent.store_id == store_id)
    if device_id:
        q = q.filter(CctvEvent.cctv_device_id == device_id)
    if from_:
        q = q.filter(CctvEvent.created_at >= from_)
    if to:
        q = q.filter(CctvEvent.created_at < to)
    events = q.order_by(CctvEvent.created_at.desc()).all()
    return [add_signed_urls_to_event(ev) for ev in events]

@router.get("/cctv/events/{event_id}", response_model=CctvEventOut)
def get_cctv_event(event_id: int, db: Session = Depends(get_db)):
    ev = db.query(CctvEvent).options(joinedload(CctvEvent.clips)).filter(CctvEvent.event_id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="event not found")
    return add_signed_urls_to_event(ev)

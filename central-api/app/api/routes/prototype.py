from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import PrototypeSet, PrototypeSetStatus
from app.schemas.prototype import (
    ActivatePrototypeSetIn,
    ActivatePrototypeSetOut,
    ActivePrototypeSetOut,
    PrototypeSetCreate,
    PrototypeSetOut,
)

router = APIRouter(dependencies=[Depends(require_admin_key)])


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.get("/prototype-sets", response_model=list[PrototypeSetOut])
def list_sets(db: Session = Depends(get_db)):
    return db.query(PrototypeSet).order_by(PrototypeSet.prototype_set_id.desc()).all()


@router.post("/prototype-sets", response_model=PrototypeSetOut)
def create_set(body: PrototypeSetCreate, db: Session = Depends(get_db)):
    s = PrototypeSet(
        status=PrototypeSetStatus(body.status),
        notes=body.notes,
        created_at=utcnow(),
        index_npy_gcs_uri=body.index_npy_gcs_uri,
        index_meta_gcs_uri=body.index_meta_gcs_uri,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.post("/prototype-sets/activate", response_model=ActivatePrototypeSetOut)
def activate_set(body: ActivatePrototypeSetIn, db: Session = Depends(get_db)):
    target = (
        db.query(PrototypeSet)
        .filter(PrototypeSet.prototype_set_id == body.prototype_set_id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="prototype_set not found")

    # 단일 ACTIVE 정책
    db.query(PrototypeSet).update({PrototypeSet.status: PrototypeSetStatus.INACTIVE})
    target.status = PrototypeSetStatus.ACTIVE

    db.commit()
    return ActivatePrototypeSetOut(ok=True, active_prototype_set_id=int(target.prototype_set_id))


@router.get("/prototype-sets/active", response_model=ActivePrototypeSetOut)
def get_active_set(db: Session = Depends(get_db)):
    active = (
        db.query(PrototypeSet)
        .filter(PrototypeSet.status == PrototypeSetStatus.ACTIVE)
        .order_by(PrototypeSet.created_at.desc())
        .first()
    )
    if not active:
        raise HTTPException(status_code=404, detail="active prototype_set not found")
    return active

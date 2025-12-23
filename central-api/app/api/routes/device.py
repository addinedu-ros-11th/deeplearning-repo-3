from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import Store, Device, DeviceType
from app.schemas.device import DeviceOut

router = APIRouter(dependencies=[Depends(require_admin_key)])

@router.get("/stores/{store_code}/devices", response_model=list[DeviceOut])
def list_devices(store_code: str, type: DeviceType | None = None, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    q = db.query(Device).filter(Device.store_id == store.store_id)
    if type:
        q = q.filter(Device.device_type == type)
    return q.order_by(Device.device_id.asc()).all()

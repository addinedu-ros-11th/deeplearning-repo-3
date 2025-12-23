from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import Store
from app.schemas.store import StoreOut

router = APIRouter(dependencies=[Depends(require_admin_key)])

@router.get("/stores", response_model=list[StoreOut])
def list_stores(db: Session = Depends(get_db)):
    return db.query(Store).order_by(Store.store_id.asc()).all()

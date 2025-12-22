from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import MenuItem
from app.schemas.menu import MenuItemOut

router = APIRouter(dependencies=[Depends(require_admin_key)])

@router.get("/menu-items", response_model=list[MenuItemOut])
def list_menu_items(active: int = 1, db: Session = Depends(get_db)):
    q = db.query(MenuItem)
    if active in (0, 1):
        q = q.filter(MenuItem.active == bool(active))
    return q.order_by(MenuItem.item_id.asc()).all()

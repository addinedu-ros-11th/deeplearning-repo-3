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

@router.get("/menu-items/{name}", response_model=MenuItemOut)
def get_menu_item_by_name(name: str, db: Session = Depends(get_db)):
    """이름(영문 또는 한글)으로 메뉴 아이템 조회"""
    from fastapi import HTTPException
    item = db.query(MenuItem).filter(
        (MenuItem.name_eng == name) | (MenuItem.name_kor == name)
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Menu item '{name}' not found")
    return item

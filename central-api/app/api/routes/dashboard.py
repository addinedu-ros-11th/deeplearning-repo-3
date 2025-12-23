from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import Store
from app.schemas.dashboard import TopMenuRow

router = APIRouter(dependencies=[Depends(require_admin_key)])

@router.get("/dashboards/top-menu", response_model=list[TopMenuRow])
def top_menu(
    store_code: str,
    from_: datetime,
    to: datetime,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    sql = text("""
        SELECT
          ol.item_id AS item_id,
          mi.name AS name,
          SUM(ol.qty) AS qty,
          SUM(ol.line_amount_won) AS amount_won
        FROM order_hdr oh
        JOIN order_line ol ON ol.order_id = oh.order_id
        JOIN menu_item mi ON mi.item_id = ol.item_id
        WHERE oh.store_id = :store_id
          AND oh.status = 'PAID'
          AND oh.created_at >= :from_
          AND oh.created_at < :to_
        GROUP BY ol.item_id, mi.name
        ORDER BY qty DESC
        LIMIT :limit
    """)
    rows = db.execute(sql, {"store_id": store.store_id, "from_": from_, "to_": to, "limit": limit}).mappings().all()
    return [TopMenuRow(**dict(r)) for r in rows]

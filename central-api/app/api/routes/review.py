from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import Review, ReviewStatus
from app.schemas.review import ReviewOut, ReviewCreate, ReviewUpdate
from app.db.models import (
    TraySession, TraySessionStatus,
    OrderHdr, OrderLine, OrderStatus,
    MenuItem, Store, Device,
)

router = APIRouter(dependencies=[Depends(require_admin_key)])

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def _set_enum_or_str(obj, field: str, enum_value):
    # 컬럼이 Enum이든 str이든 안전하게 할당
    try:
        setattr(obj, field, enum_value)
    except Exception:
        setattr(obj, field, getattr(enum_value, "value", str(enum_value)))

def _parse_confirmed_items(confirmed_items_json) -> dict[int, int]:
    """
    expected:
      confirmed_items_json = [{ "item_id": 101, "qty": 2 }, ...]
    return:
      { item_id: total_qty }
    """
    if not confirmed_items_json:
        return {}

    if not isinstance(confirmed_items_json, list):
        return {}

    out: dict[int, int] = {}
    for row in confirmed_items_json:
        if not isinstance(row, dict):
            continue
        item_id = row.get("item_id")
        qty = row.get("qty", 1)
        try:
            item_id_i = int(item_id)
            qty_i = int(qty)
        except Exception:
            continue
        if item_id_i <= 0 or qty_i <= 0:
            continue
        out[item_id_i] = out.get(item_id_i, 0) + qty_i
    return out

def _ensure_order_for_session(db: Session, session_id: int, store_id: int, item_qty: dict[int, int]) -> OrderHdr:
    """
    이미 주문이 있으면 그대로 반환.
    없으면 menu_item.price_won으로 주문 생성.
    """
    existing = db.query(OrderHdr).filter(OrderHdr.session_id == session_id).first()
    if existing:
        return existing

    if not item_qty:
        raise ValueError("confirmed_items_json is empty")

    menu_rows = db.query(MenuItem).filter(MenuItem.item_id.in_(list(item_qty.keys()))).all()
    price_map = {m.item_id: int(m.price_won) for m in menu_rows}

    missing = [iid for iid in item_qty.keys() if iid not in price_map]
    if missing:
        raise ValueError(f"price not found for item_ids={missing}")

    now = utcnow()
    order = OrderHdr(
        store_id=store_id,
        session_id=session_id,
        total_amount_won=0,
        status=OrderStatus.PAID,
        created_at=now,
    )
    db.add(order)
    db.flush()  # order_id 확보

    total = 0
    for iid, qty in item_qty.items():
        unit = price_map[iid]
        line_amount = unit * qty
        total += line_amount
        db.add(
            OrderLine(
                order_id=order.order_id,
                item_id=iid,
                qty=qty,
                unit_price_won=unit,
                line_amount_won=line_amount,
            )
        )

    order.total_amount_won = total
    return order

def _enrich_review(review: Review, db: Session) -> dict:
    """리뷰에 매장/디바이스 정보 추가"""
    top_k_with_names = review.top_k_json
    if isinstance(review.top_k_json, list) and review.top_k_json:
        item_ids = [item.get("item_id") for item in review.top_k_json if isinstance(item, dict) and item.get("item_id")]
        if item_ids:
            menu_rows = db.query(MenuItem).filter(MenuItem.item_id.in_(item_ids)).all()
            name_map = {m.item_id: m.name_kor for m in menu_rows}
            top_k_with_names = []
            for item in review.top_k_json:
                if isinstance(item, dict):
                    enriched = dict(item)
                    item_id = item.get("item_id")
                    if item_id and item_id in name_map:
                        enriched["name_kor"] = name_map[item_id]
                    top_k_with_names.append(enriched)

    result = {
        "review_id": review.review_id,
        "session_id": review.session_id,
        "run_id": review.run_id,
        "status": review.status,
        "reason": review.reason,
        "top_k_json": top_k_with_names,
        "confirmed_items_json": review.confirmed_items_json,
        "created_at": review.created_at,
        "resolved_at": review.resolved_at,
        "resolved_by": review.resolved_by,
        "store_name": None,
        "device_code": None,
    }

    # 세션에서 매장/디바이스 정보 조회
    session = db.query(TraySession).filter(TraySession.session_id == review.session_id).first()
    if session:
        store = db.query(Store).filter(Store.store_id == session.store_id).first()
        device = db.query(Device).filter(Device.device_id == session.checkout_device_id).first()
        if store:
            result["store_name"] = store.name
        if device:
            result["device_code"] = device.device_code

    return result

@router.get("/reviews", response_model=list[ReviewOut])
def list_reviews(status: ReviewStatus | None = ReviewStatus.OPEN, db: Session = Depends(get_db)):
    q = db.query(Review)
    if status:
        q = q.filter(Review.status == status)
    reviews = q.order_by(Review.created_at.desc()).all()
    return [_enrich_review(r, db) for r in reviews]

@router.post("/reviews", response_model=ReviewOut)
def create_review(body: ReviewCreate, db: Session = Depends(get_db)):
    """관리자 호출 등 수동 리뷰 생성"""
    # 세션 존재 확인
    session = db.query(TraySession).filter(TraySession.session_id == body.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    review = Review(
        session_id=body.session_id,
        run_id=None,
        status=ReviewStatus.OPEN,
        reason=body.reason,
        created_at=utcnow(),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return _enrich_review(review, db)

@router.get("/reviews/{review_id}", response_model=ReviewOut)
def get_review(review_id: int, db: Session = Depends(get_db)):
    r = db.query(Review).filter(Review.review_id == review_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="review not found")
    return _enrich_review(r, db)

@router.patch("/reviews/{review_id}", response_model=ReviewOut)
def update_review(review_id: int, body: ReviewUpdate, db: Session = Depends(get_db)):
    r = db.query(Review).filter(Review.review_id == review_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="review not found")

    if r.status == ReviewStatus.RESOLVED and body.status == ReviewStatus.OPEN:
        raise HTTPException(status_code=400, detail="cannot reopen resolved review")

    # RESOLVED로 바꾸는 순간: 주문 생성 + 세션 종료까지 원자적으로 수행
    if body.status == ReviewStatus.RESOLVED:
        # ADMIN_CALL, UNKNOWN review는 주문 없이 단순 확인 처리
        if r.reason in ("ADMIN_CALL", "UNKNOWN"):
            r.status = ReviewStatus.RESOLVED
            r.resolved_at = utcnow()
            r.resolved_by = body.resolved_by
            r.confirmed_items_json = body.confirmed_items_json
            db.commit()
            db.refresh(r)
            return _enrich_review(r, db)

        if not body.confirmed_items_json:
            raise HTTPException(status_code=400, detail="confirmed_items_json required for RESOLVED")

        item_qty = _parse_confirmed_items(body.confirmed_items_json)
        if not item_qty:
            raise HTTPException(status_code=400, detail="confirmed_items_json invalid/empty")

        s = db.query(TraySession).filter(TraySession.session_id == r.session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="tray session not found for review")

        # 세션이 이미 PAID면: idempotent 처리(주문만 확인하고 review를 RESOLVED로 마감 가능)
        # ACTIVE가 아니면서 PAID도 아니면(예: CANCELLED/TIMEOUT): 결제 확정 불가
        if str(getattr(s, "status")) not in (str(TraySessionStatus.ACTIVE), str(TraySessionStatus.PAID)):
            raise HTTPException(status_code=400, detail=f"cannot resolve review when session status={s.status}")

        try:
            # (1) 주문 생성(또는 기존 주문 재사용)
            order = _ensure_order_for_session(db, s.session_id, s.store_id, item_qty)

            # (2) 세션 종료(PAID) - 이미 PAID면 유지
            if str(getattr(s, "status")) != str(TraySessionStatus.PAID):
                _set_enum_or_str(s, "status", TraySessionStatus.PAID)
                s.ended_at = utcnow()
                s.end_reason = "PAID"
                db.add(s)

            # (3) 리뷰 마감
            r.status = ReviewStatus.RESOLVED
            r.resolved_at = utcnow()
            r.resolved_by = body.resolved_by
            r.confirmed_items_json = body.confirmed_items_json

            db.add(r)
            db.commit()
            db.refresh(r)
            return r

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"resolve failed: {e}")

    # RESOLVED가 아닌 일반 업데이트(예: OPEN 유지/사유 수정 등)
    r.status = body.status
    db.commit()
    db.refresh(r)
    return r

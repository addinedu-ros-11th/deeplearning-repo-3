from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import TraySession, OrderHdr, OrderLine, OrderStatus, DecisionState, RecognitionRun, Review, ReviewStatus, TraySessionStatus
from app.schemas.order import OrderHdrOut, OrderCreate, TraySessionCreate

router = APIRouter(dependencies=[Depends(require_admin_key)])

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

@router.post("/sessions/create")
def create_session(body: TraySessionCreate, db: Session = Depends(get_db)):
    session = TraySession(
        session_uuid=body.session_uuid,
        store_id=body.store_id,
        checkout_device_id=body.checkout_device_id,
        status=TraySessionStatus.ACTIVE,  # 적절한 초기 상태
        attempt_limit=body.attempt_limit,
        started_at=utcnow(),
        created_at=utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "session_id": session.session_id,
        "session_uuid": session.session_uuid,
        "status": session.status
    }

@router.post("/orders/save", response_model=OrderHdrOut)
def save_order(body: OrderCreate, db: Session = Depends(get_db)):
    # TraySession 존재 확인
    session = db.query(TraySession).filter(
        TraySession.session_id == body.session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404, 
            detail="Tray session not found"
        )
    
    # 세션 상태 확인 (이미 종료된 세션인지 등)
    if session.status != TraySessionStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Session is not active: {session.status}"
        )
    
    # 이미 주문이 있는지 확인
    existing_order = db.query(OrderHdr).filter(
        OrderHdr.session_id == body.session_id
    ).first()
    
    if existing_order:
        raise HTTPException(
            status_code=400, 
            detail="Order already exists for this session"
        )
    
    # OrderHdr 생성
    order = OrderHdr(
        store_id=body.store_id,
        session_id=body.session_id,
        total_amount_won=body.total_amount_won,
        status=OrderStatus.PENDING,
        created_at=utcnow()
    )
    db.add(order)
    db.flush()
    
    # OrderLine들 생성
    for line_data in body.lines:
        order_line = OrderLine(
            order_id=order.order_id,
            item_id=line_data.item_id,
            qty=line_data.qty,
            unit_price_won=line_data.unit_price_won,
            line_amount_won=line_data.line_amount_won
        )
        db.add(order_line)
    
    # 세션 상태 업데이트 (주문 완료)
    session.status = TraySessionStatus.COMPLETED  # 또는 적절한 상태
    session.ended_at = utcnow()
    session.end_reason = "ORDER_COMPLETED"
    
    db.commit()
    db.refresh(order)
    
    return order

@router.get("/orders", response_model=list[OrderHdrOut])
def list_orders(store_id: int | None = None, from_: datetime | None = None, to: datetime | None = None, db: Session = Depends(get_db)):
    q = db.query(OrderHdr).options(joinedload(OrderHdr.lines))
    if store_id:
        q = q.filter(OrderHdr.store_id == store_id)
    if from_:
        q = q.filter(OrderHdr.created_at >= from_)
    if to:
        q = q.filter(OrderHdr.created_at < to)
    return q.order_by(OrderHdr.created_at.desc()).all()

@router.get("/orders/{order_id}", response_model=OrderHdrOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.query(OrderHdr).options(joinedload(OrderHdr.lines)).filter(OrderHdr.order_id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="order not found")
    return o

# @router.post("/tray-sessions/{session_uuid}/orders", response_model=OrderHdrOut)
# def create_order_for_session(session_uuid: str, body: OrderCreate, db: Session = Depends(get_db)):
    # s = db.query(TraySession).filter(TraySession.session_uuid == session_uuid).first()
    # if not s:
    #     raise HTTPException(status_code=404, detail="session not found")

    # open_review = db.query(Review).filter(Review.session_id == s.session_id, Review.status == ReviewStatus.OPEN).first()
    # if open_review:
    #     raise HTTPException(status_code=400, detail="cannot create order: review exists")

    # last_run = (
    #     db.query(RecognitionRun)
    #     .filter(RecognitionRun.session_id == s.session_id)
    #     .order_by(RecognitionRun.attempt_no.desc())
    #     .first()
    # )
    # if not last_run:
    #     raise HTTPException(status_code=400, detail="no recognition run")
    # if last_run.decision != DecisionState.AUTO:
    #     raise HTTPException(status_code=400, detail="cannot create order: decision is not AUTO")

    # exists = db.query(OrderHdr).filter(OrderHdr.session_id == s.session_id).first()
    # if exists:
    #     raise HTTPException(status_code=409, detail="order already exists for this session")

    # total = 0
    # lines = []
    # for it in body.items:
    #     line_amount = it.qty * it.unit_price_won
    #     total += line_amount
    #     lines.append(OrderLine(
    #         item_id=it.item_id,
    #         qty=it.qty,
    #         unit_price_won=it.unit_price_won,
    #         line_amount_won=line_amount,
    #     ))

    # o = OrderHdr(
    #     store_id=s.store_id,
    #     session_id=s.session_id,
    #     total_amount_won=total,
    #     status=OrderStatus.PAID,
    #     created_at=utcnow(),
    #     lines=lines,
    # )
    # db.add(o)
    # db.commit()
    # db.refresh(o)
    # return o

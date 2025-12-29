from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import ORMBase
from app.db.models import OrderStatus

class TraySessionCreate(BaseModel):
    store_id: int
    checkout_device_id: int
    session_uuid: str
    attempt_limit: int = 3  # 기본값

class OrderLineIn(BaseModel):
    item_id: int
    qty: int = Field(ge=1)
    unit_price_won: int = Field(ge=0)

class OrderCreate(BaseModel):
    items: list[OrderLineIn]

class OrderLineOut(ORMBase):
    order_line_id: int
    order_id: int
    item_id: int
    item_name: str | None = None  # 메뉴 아이템 이름
    qty: int
    unit_price_won: int
    line_amount_won: int

class OrderHdrOut(ORMBase):
    order_id: int
    store_id: int
    store_name: str | None = None  # 매장 이름
    session_id: int
    total_amount_won: int
    status: OrderStatus
    created_at: datetime
    lines: list[OrderLineOut] = []

class OrderLineCreate(BaseModel):
    item_id: int
    qty: int
    unit_price_won: int
    line_amount_won: int

class OrderCreate(BaseModel):
    store_id: int
    session_id: int
    total_amount_won: int
    lines: list[OrderLineCreate]

from datetime import datetime
from app.schemas.common import ORMBase

class MenuItemOut(ORMBase):
    item_id: int
    name_eng: str
    name_kor: str
    category_id: int | None = None
    price_won: int
    weight_grams: int | None = None
    active: bool
    created_at: datetime

from datetime import datetime
from app.schemas.common import ORMBase

class StoreOut(ORMBase):
    store_id: int
    store_code: str
    name: str
    created_at: datetime

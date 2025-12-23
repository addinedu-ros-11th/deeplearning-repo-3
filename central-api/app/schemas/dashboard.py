from pydantic import BaseModel

class TopMenuRow(BaseModel):
    item_id: int
    name: str
    qty: int
    amount_won: int

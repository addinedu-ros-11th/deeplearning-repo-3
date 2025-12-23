from datetime import datetime
from typing import Any
from pydantic import BaseModel
from app.schemas.common import ORMBase
from app.db.models import ReviewStatus

class ReviewOut(ORMBase):
    review_id: int
    session_id: int
    run_id: int | None = None
    status: ReviewStatus
    reason: str
    top_k_json: Any | None = None
    confirmed_items_json: Any | None = None
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None

class ReviewUpdate(BaseModel):
    status: ReviewStatus
    resolved_by: str | None = None
    confirmed_items_json: Any | None = None

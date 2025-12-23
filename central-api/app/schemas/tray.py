from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from app.schemas.common import ORMBase
from app.db.models import TraySessionStatus, DecisionState

class TraySessionCreate(BaseModel):
    session_uuid: str | None = None
    attempt_limit: int = 3

class TraySessionOut(ORMBase):
    session_id: int
    session_uuid: str
    store_id: int
    checkout_device_id: int
    status: TraySessionStatus
    attempt_limit: int
    started_at: datetime
    ended_at: datetime | None = None
    end_reason: str | None = None
    created_at: datetime

class RecognitionRunCreate(BaseModel):
    attempt_no: int = Field(ge=1, le=3)
    overlap_score: float | None = None
    decision: DecisionState
    result_json: Any

class RecognitionRunOut(ORMBase):
    run_id: int
    session_id: int
    attempt_no: int
    overlap_score: float | None = None
    decision: DecisionState
    result_json: Any
    created_at: datetime

from datetime import datetime
from typing import Any
from pydantic import BaseModel
from app.schemas.common import ORMBase
from app.db.models import CctvEventType, CctvEventStatus

class CctvClipIn(BaseModel):
    clip_gcs_uri: str
    clip_start_at: datetime
    clip_end_at: datetime

class CctvEventCreate(BaseModel):
    event_type: CctvEventType
    confidence: float
    status: CctvEventStatus = CctvEventStatus.OPEN
    started_at: datetime
    ended_at: datetime
    meta_json: Any | None = None
    clip: CctvClipIn

class CctvEventClipOut(ORMBase):
    clip_id: int
    event_id: int
    clip_gcs_uri: str
    clip_start_at: datetime
    clip_end_at: datetime
    created_at: datetime

class CctvEventOut(ORMBase):
    event_id: int
    store_id: int
    cctv_device_id: int
    event_type: CctvEventType
    confidence: float
    status: CctvEventStatus
    started_at: datetime
    ended_at: datetime
    meta_json: Any | None = None
    created_at: datetime
    clips: list[CctvEventClipOut] = []

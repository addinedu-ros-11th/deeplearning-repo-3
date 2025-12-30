from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from app.db.models import PrototypeSetStatus


class PrototypeSetCreate(BaseModel):
    """통합 PrototypeSet 생성.

    - 메뉴별 prototype row는 두지 않고, 통합 인덱스(25개 전체) 아티팩트만 관리한다.
    - index_npy_gcs_uri / index_meta_gcs_uri는 반드시 Central/AI가 접근 가능한 URI여야 한다.
    """

    status: PrototypeSetStatus = Field(..., description="ACTIVE/INACTIVE")
    notes: str | None = None

    # ✅ 통합 인덱스(25개 전체) 아티팩트 위치
    index_npy_gcs_uri: str = Field(..., max_length=512)
    index_meta_gcs_uri: str = Field(..., max_length=512)


class PrototypeSetOut(BaseModel):
    prototype_set_id: int
    status: PrototypeSetStatus
    notes: str | None
    created_at: datetime

    index_npy_gcs_uri: str
    index_meta_gcs_uri: str

    class Config:
        from_attributes = True


class ActivatePrototypeSetIn(BaseModel):
    prototype_set_id: int


class ActivatePrototypeSetOut(BaseModel):
    ok: bool
    active_prototype_set_id: int


class ActivePrototypeSetOut(PrototypeSetOut):
    """현재 ACTIVE인 prototype_set."""

    pass

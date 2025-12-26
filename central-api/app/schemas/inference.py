from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, Optional

class TrayResultIngestRequest(BaseModel):
    session_uuid: str
    attempt_no: int = Field(ge=1, le=3)

    store_code: str
    device_code: str  # CHECKOUT device_code (POS-01)

    overlap_score: float | None = None
    decision: str = Field(..., description="AUTO/REVIEW/UNKNOWN")
    result_json: dict[str, Any]

class TrayResultIngestResponse(BaseModel):
    session_id: int
    run_id: int
    created_review_id: Optional[int] = None

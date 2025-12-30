from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORMBase
from app.db.models import DecisionState, InferenceJobStatus, InferenceJobType


class TrayIngestRequest(BaseModel):
    """
    Central에 추론 결과를 '직접 ingest'하는 payload (레거시/디버그용).
    - 메인 경로(B안): /inference/tray/jobs -> claim(poll) -> complete
    - 본 payload는 이미지 업로드를 포함하지 않고 결과(result_json)만 저장한다.
    - result_json 안에는 polygon/bbox/center/top_k 등을 포함할 수 있음
    """
    # attempt_no는 정책상 남겨둠(최대 3) — 추후 재시도/디버그/로그 정렬에 유용
    attempt_no: int = Field(..., ge=1, le=3)

    # session이 Central에 아직 없다면 auto-create에 필요
    store_code: str | None = None
    device_code: str | None = None

    # AI 판단 요약
    overlap_score: float | None = None
    decision: DecisionState

    # 상세 결과(원문 그대로 저장)
    # 기대 구조 예:
    # {
    #   "instances":[
    #      {"instance_id":1,"best_item_id":101,"confidence":0.92,"qty":1,"state":"AUTO",
    #       "bbox":[x1,y1,x2,y2], "mask_poly":[[x,y],...], "center":[cx,cy],
    #       "top_k":[{"item_id":101,"distance":0.14},...]
    #      }
    #   ],
    #   "items":[{"item_id":101,"qty":1}]
    # }
    result_json: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate(self):
        # 최소한 instances는 있어야 오버레이/리뷰에서 의미가 있음
        if "instances" in self.result_json and not isinstance(self.result_json["instances"], list):
            raise ValueError("result_json.instances must be a list if provided")
        return self


class TrayIngestResponse(BaseModel):
    run_id: int
    session_uuid: str
    attempt_no: int

    overlap_score: float | None = None
    decision: Literal["AUTO", "REVIEW", "UNKNOWN"]
    result_json: dict[str, Any]


class TrayLatestResponse(BaseModel):
    """
    키오스크/관리자 UI가 Central에서 최신 결과를 재조회할 때 사용(선택).
    """
    session_uuid: str
    attempt_no: int
    decision: Literal["AUTO", "REVIEW", "UNKNOWN"]
    overlap_score: float | None = None
    result_json: dict[str, Any]


class CctvIngestRequest(BaseModel):
    store_code: str
    device_code: str
    events: list[dict[str, Any]] = Field(default_factory=list)
    clip_gcs_uri: str | None = None


class CctvIngestResponse(BaseModel):
    created_event_ids: list[int] = Field(default_factory=list)


# =====================
# Inference Job (TRAY)
# =====================
class TrayJobCreate(BaseModel):
    store_code: str
    device_code: str
    session_uuid: str | None = None

    # 둘 중 하나만 허용
    frame_b64: str | None = None
    frame_gcs_uri: str | None = None

    @model_validator(mode="after")
    def _validate(self):
        if not self.frame_b64 and not self.frame_gcs_uri:
            raise ValueError("Either frame_b64 or frame_gcs_uri is required")
        if self.frame_b64 and self.frame_gcs_uri:
            raise ValueError("Provide only one of frame_b64 or frame_gcs_uri")
        return self


class TrayJobOut(ORMBase):
    job_id: int
    job_type: InferenceJobType
    status: InferenceJobStatus

    store_id: int
    device_id: int
    session_id: int | None = None
    session_uuid: str | None = None
    attempt_no: int | None = None

    frame_gcs_uri: str

    # 결과(완료 후)
    run_id: int | None = None
    decision: DecisionState | None = None
    result_json: dict[str, Any] | None = None
    error: str | None = None

    # 워커 추적
    worker_id: str | None = None
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class TrayJobClaimRequest(BaseModel):
    worker_id: str = Field(..., min_length=1, max_length=64)


class TrayJobCompleteRequest(BaseModel):
    # AI 결과
    overlap_score: float | None = None
    decision: Literal["AUTO", "REVIEW", "UNKNOWN"]
    result_json: dict[str, Any]
    error: str | None = None

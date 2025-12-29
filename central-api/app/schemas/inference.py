from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

from app.db.models import DecisionState


class TrayIngestRequest(BaseModel):
    """
    로컬 AI(ai-inference) 또는 kiosk-agent가 Central로 업로드하는 payload.
    - 이미지는 업로드하지 않음(옵션 A): 결과 좌표/라벨만 업로드
    - 단, result_json 안에는 polygon/bbox/center/top_k 등을 포함할 수 있음
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
    # clip은 로컬 저장 정책이면 중앙에는 경로/메타만 올려도 됨
    clip_local_path: str | None = None


class CctvIngestResponse(BaseModel):
    created_event_ids: list[int] = Field(default_factory=list)

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import (
    TraySession,
    TraySessionStatus,
    RecognitionRun,
    DecisionState,
    Review,
    ReviewStatus,
    Store,
    Device,
    DeviceType,
    MenuItem,
)

from app.schemas.inference import TrayIngestRequest, TrayIngestResponse, TrayLatestResponse


router = APIRouter(dependencies=[Depends(require_admin_key)])


def utcnow_naive() -> datetime:
    # DB는 UTC naive로 통일(정책)
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _compute_center_from_bbox(bbox: list[float] | list[int]) -> list[float] | None:
    if not isinstance(bbox, list) or len(bbox) != 4:
        return None
    x1, y1, x2, y2 = bbox
    return [float(x1 + x2) / 2.0, float(y1 + y2) / 2.0]


def _compute_center_from_poly(poly: list[list[float]] | list[list[int]]) -> list[float] | None:
    if not isinstance(poly, list) or len(poly) < 3:
        return None
    xs = []
    ys = []
    for p in poly:
        if not isinstance(p, list) or len(p) != 2:
            continue
        xs.append(float(p[0]))
        ys.append(float(p[1]))
    if not xs:
        return None
    return [sum(xs) / len(xs), sum(ys) / len(ys)]


def _augment_instances_with_center_and_label(db: Session, result_json: dict[str, Any]) -> dict[str, Any]:
    """
    - center가 없으면 bbox/polygon으로 계산해서 넣음
    - best_item_id가 있으면 menu_item.name을 label_text로 넣음
    - 키오스크는 기본적으로 label_text + center만 렌더링하고,
      토글 ON이면 bbox/mask_poly를 렌더링하면 됨
    """
    instances = result_json.get("instances")
    if not isinstance(instances, list) or not instances:
        return result_json

    # best_item_id 수집 -> 이름 매핑
    ids: set[int] = set()
    for inst in instances:
        if isinstance(inst, dict):
            bid = inst.get("best_item_id")
            if isinstance(bid, int):
                ids.add(bid)

    name_map: dict[int, str] = {}
    if ids:
        rows = db.query(MenuItem).filter(MenuItem.item_id.in_(list(ids))).all()
        name_map = {int(r.item_id): r.name for r in rows}

    for inst in instances:
        if not isinstance(inst, dict):
            continue

        # label_text
        bid = inst.get("best_item_id")
        if isinstance(bid, int) and "label_text" not in inst:
            inst["label_text"] = name_map.get(bid, f"ITEM-{bid}")

        # center
        if "center" not in inst or not inst.get("center"):
            center = None
            poly = inst.get("mask_poly")
            bbox = inst.get("bbox")
            if isinstance(poly, list):
                center = _compute_center_from_poly(poly)
            if not center and isinstance(bbox, list):
                center = _compute_center_from_bbox(bbox)
            if center:
                inst["center"] = center

    result_json["instances"] = instances
    return result_json


@router.post("/tray-sessions/{session_uuid}/infer", response_model=TrayIngestResponse)
def ingest_tray_inference(
    session_uuid: str,
    body: TrayIngestRequest,
    db: Session = Depends(get_db),
):
    """
    (중요) 예전에는 Central이 AI를 호출했지만,
    이제는 로컬 AI/에이전트가 만든 결과를 Central이 저장(ingest)한다.

    - session이 없으면 (store_code, device_code)로 자동 생성 가능
    - recognition_run 생성
    - decision이 REVIEW/UNKNOWN이면 review OPEN 생성(없을 때만)
    """
    s = db.query(TraySession).filter(TraySession.session_uuid == session_uuid).first()

    # 세션이 없으면 auto-create (옵션)
    if not s:
        if not body.store_code or not body.device_code:
            raise HTTPException(
                status_code=404,
                detail="session not found; provide store_code/device_code to auto-create session",
            )

        st = db.query(Store).filter(Store.store_code == body.store_code).first()
        if not st:
            raise HTTPException(status_code=404, detail="store not found")

        dv = (
            db.query(Device)
            .filter(Device.store_id == st.store_id)
            .filter(Device.device_code == body.device_code)
            .filter(Device.device_type == DeviceType.CHECKOUT)
            .first()
        )
        if not dv:
            raise HTTPException(status_code=404, detail="checkout device not found")

        s = TraySession(
            session_uuid=session_uuid,
            store_id=st.store_id,
            checkout_device_id=dv.device_id,
            status=TraySessionStatus.ACTIVE,
            attempt_limit=3,
            started_at=utcnow_naive(),
            ended_at=None,
            end_reason=None,
            created_at=utcnow_naive(),
        )
        db.add(s)
        db.commit()
        db.refresh(s)

    # attempt 제한
    if body.attempt_no > int(s.attempt_limit):
        raise HTTPException(status_code=400, detail="attempt limit exceeded")

    # attempt_no 중복 방지
    exists = (
        db.query(RecognitionRun)
        .filter(RecognitionRun.session_id == s.session_id)
        .filter(RecognitionRun.attempt_no == body.attempt_no)
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="this attempt_no already exists")

    # 결과 보강(center/label_text)
    result_json = body.result_json or {}
    result_json = _augment_instances_with_center_and_label(db, result_json)

    run = RecognitionRun(
        session_id=s.session_id,
        attempt_no=body.attempt_no,
        overlap_score=body.overlap_score,
        decision=DecisionState(str(body.decision)),
        result_json=result_json,
        created_at=utcnow_naive(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # REVIEW / UNKNOWN이면 review OPEN 생성(세션당 1개 OPEN 정책)
    dec = str(body.decision)
    if dec in ("REVIEW", "UNKNOWN"):
        open_review = (
            db.query(Review)
            .filter(Review.session_id == s.session_id)
            .filter(Review.status == ReviewStatus.OPEN)
            .first()
        )
        if not open_review:
            top_k_compact = None
            try:
                # instances[0].top_k 등을 관리자가 보기 쉽게 올릴 수 있음(선택)
                insts = result_json.get("instances") or []
                if isinstance(insts, list) and insts:
                    top_k_compact = insts[0].get("top_k")
            except Exception:
                top_k_compact = None

            r = Review(
                session_id=s.session_id,
                run_id=run.run_id,
                status=ReviewStatus.OPEN,
                reason=dec,                 # REVIEW / UNKNOWN
                top_k_json=top_k_compact,   # optional
                confirmed_items_json=None,
                created_at=utcnow_naive(),
                resolved_at=None,
                resolved_by=None,
            )
            db.add(r)
            db.commit()

    return TrayIngestResponse(
        run_id=int(run.run_id),
        session_uuid=session_uuid,
        attempt_no=int(run.attempt_no),
        overlap_score=run.overlap_score,
        decision=str(run.decision),
        result_json=run.result_json or {},
    )


@router.get("/tray-sessions/{session_uuid}/infer/latest", response_model=TrayLatestResponse)
def get_latest_tray_inference(session_uuid: str, db: Session = Depends(get_db)):
    """
    키오스크/관리자 UI가 중앙에서 최신 결과를 다시 가져오고 싶을 때(선택).
    - 네트워크/에이전트 문제로 UI에 결과가 유실되어도 복구 가능
    """
    s = db.query(TraySession).filter(TraySession.session_uuid == session_uuid).first()
    if not s:
        raise HTTPException(status_code=404, detail="session not found")

    last = (
        db.query(RecognitionRun)
        .filter(RecognitionRun.session_id == s.session_id)
        .order_by(RecognitionRun.attempt_no.desc())
        .first()
    )
    if not last:
        raise HTTPException(status_code=404, detail="no recognition run")

    return TrayLatestResponse(
        session_uuid=session_uuid,
        attempt_no=int(last.attempt_no),
        decision=str(last.decision),
        overlap_score=last.overlap_score,
        result_json=last.result_json or {},
    )

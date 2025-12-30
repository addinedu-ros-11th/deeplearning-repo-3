from __future__ import annotations

import base64
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import (
    InferenceJob,
    InferenceJobStatus,
    InferenceJobType,
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

from app.schemas.inference import (
    TrayIngestRequest,
    TrayIngestResponse,
    TrayLatestResponse,
    TrayJobCreate,
    TrayJobOut,
    TrayJobClaimRequest,
    TrayJobClaimResponse,
    TrayJobCompleteRequest,
)

from app.services.gcs import upload_bytes


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
    (중요) Central은 추론을 "직접 호출"하지 않는다.
    현재 운영 흐름(B안)은 Central Job Queue를 경유한다.

    - PyQt/Kiosk: /inference/tray/jobs 로 추론 요청(Job) 생성
      * frame_b64를 보내면 Central이 GCS에 업로드하고 frame_gcs_uri를 확정
      * 또는 이미 업로드된 frame_gcs_uri로 Job 생성 가능

    - AI Worker(로컬 서버 #2): /inference/tray/jobs/claim 으로 PENDING Job을 Polling(Pull)
      * frame_gcs_uri의 이미지를 내려받아 로컬에서 추론 수행

    - 완료 업로드: /inference/tray/jobs/{job_id}/complete 로 결과를 Central에 저장
      * RecognitionRun 생성
      * decision이 REVIEW/UNKNOWN이면 Review OPEN 생성(세션당 1개 OPEN 정책)

    이 엔드포인트(/tray-sessions/{session_uuid}/infer)는
    '결과를 바로 ingest'하는 직접 업로드 경로(레거시/디버그용)로 유지할 수 있다.
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


# =====================
# Job Queue (TRAY)
# - PyQt/Kiosk: job 생성(이미지 b64 or gcs_uri)
# - AI Worker(로컬 GPU): job 클레임 -> 추론 -> complete로 결과 업로드
# =====================
def _ensure_tray_session(db: Session, store_code: str, device_code: str, session_uuid: str | None) -> TraySession:
    # store/device lookup
    st = db.query(Store).filter(Store.store_code == store_code).first()
    if not st:
        raise HTTPException(status_code=404, detail="store not found")

    dv = (
        db.query(Device)
        .filter(Device.store_id == st.store_id)
        .filter(Device.device_code == device_code)
        .filter(Device.device_type == DeviceType.CHECKOUT)
        .first()
    )
    if not dv:
        raise HTTPException(status_code=404, detail="checkout device not found")

    # get or create session
    if not session_uuid:
        session_uuid = str(uuid.uuid4())

    s = db.query(TraySession).filter(TraySession.session_uuid == session_uuid).first()
    if s:
        return s

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
    return s


def _next_attempt_no(db: Session, session_id: int) -> int:
    last = (
        db.query(RecognitionRun)
        .filter(RecognitionRun.session_id == session_id)
        .order_by(RecognitionRun.attempt_no.desc())
        .first()
    )
    return 1 if not last else (int(last.attempt_no) + 1)


@router.post("/inference/tray/jobs", response_model=TrayJobOut)
def create_tray_job(body: TrayJobCreate, db: Session = Depends(get_db)):
    """키오스크가 1장 프레임을 등록하고, AI Worker가 가져갈 수 있는 Job 생성."""
    if not settings.GCS_BUCKET_TRAY and not body.frame_gcs_uri:
        raise HTTPException(status_code=500, detail="GCS_BUCKET_TRAY is not set")

    # session 확보
    s = _ensure_tray_session(db, body.store_code, body.device_code, body.session_uuid)
    attempt_no = _next_attempt_no(db, s.session_id)
    if attempt_no > int(s.attempt_limit):
        raise HTTPException(status_code=400, detail="attempt limit exceeded")

    # frame_gcs_uri 확보
    frame_gcs_uri = body.frame_gcs_uri
    if not frame_gcs_uri:
        raw_b = base64.b64decode(_strip_data_url_prefix(body.frame_b64 or ""))
        # object name
        ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        object_name = f"tray/{body.store_code}/{body.device_code}/{s.session_uuid}/attempt_{attempt_no}/{ts}.jpg"
        frame_gcs_uri = upload_bytes(settings.GCS_BUCKET_TRAY, object_name, raw_b, content_type="image/jpeg")

    j = InferenceJob(
        job_type=InferenceJobType.TRAY,
        status=InferenceJobStatus.PENDING,
        store_id=s.store_id,
        device_id=s.checkout_device_id,
        session_id=s.session_id,
        attempt_no=attempt_no,
        frame_gcs_uri=frame_gcs_uri,
        result_json=None,
        decision=None,
        run_id=None,
        worker_id=None,
        error=None,
        created_at=utcnow_naive(),
        claimed_at=None,
        completed_at=None,
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


@router.post("/inference/tray/jobs/claim", response_model=TrayJobClaimResponse)
def claim_next_tray_job(body: TrayJobClaimRequest, db: Session = Depends(get_db)):
    """AI Worker가 가장 오래된 PENDING job을 클레임."""
    # NOTE: 데모 단일 워커 기준. 다중 워커면 for_update(skip_locked=True) 권장.
    j = (
        db.query(InferenceJob)
        .filter(InferenceJob.job_type == InferenceJobType.TRAY)
        .filter(InferenceJob.status == InferenceJobStatus.PENDING)
        .order_by(InferenceJob.created_at.asc())
        .first()
    )
    if not j:
        return TrayJobClaimResponse(job=None)

    j.status = InferenceJobStatus.CLAIMED
    j.worker_id = body.worker_id
    j.claimed_at = utcnow_naive()
    db.commit()
    db.refresh(j)
    return TrayJobClaimResponse(job=j)


@router.get("/inference/tray/jobs/{job_id}", response_model=TrayJobOut)
def get_tray_job(job_id: int, db: Session = Depends(get_db)):
    j = db.query(InferenceJob).filter(InferenceJob.job_id == job_id).first()
    if not j:
        raise HTTPException(status_code=404, detail="job not found")
    return j


@router.post("/inference/tray/jobs/{job_id}/complete", response_model=TrayJobOut)
def complete_tray_job(job_id: int, body: TrayJobCompleteRequest, db: Session = Depends(get_db)):
    j = db.query(InferenceJob).filter(InferenceJob.job_id == job_id).first()
    if not j:
        raise HTTPException(status_code=404, detail="job not found")
    if j.status not in (InferenceJobStatus.CLAIMED, InferenceJobStatus.PENDING):
        raise HTTPException(status_code=400, detail=f"job is not completable: {j.status}")

    s = db.query(TraySession).filter(TraySession.session_id == j.session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="session not found")

    # 결과 저장(RecognitionRun/Review)
    dec = body.decision
    if dec not in ("AUTO", "REVIEW", "UNKNOWN"):
        raise HTTPException(status_code=400, detail="invalid decision")

    run = RecognitionRun(
        session_id=s.session_id,
        attempt_no=int(j.attempt_no),
        overlap_score=body.overlap_score,
        decision=DecisionState(dec),
        result_json=body.result_json or {},
        created_at=utcnow_naive(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    if dec in ("REVIEW", "UNKNOWN"):
        open_review = (
            db.query(Review)
            .filter(Review.session_id == s.session_id)
            .filter(Review.status == ReviewStatus.OPEN)
            .first()
        )
        if not open_review:
            try:
                insts = (body.result_json or {}).get("instances") or []
                top_k_compact = insts[0].get("top_k") if insts else None
            except Exception:
                top_k_compact = None

            r = Review(
                session_id=s.session_id,
                run_id=run.run_id,
                status=ReviewStatus.OPEN,
                reason=dec,
                top_k_json=top_k_compact,
                confirmed_items_json=None,
                created_at=utcnow_naive(),
                resolved_at=None,
                resolved_by=None,
            )
            db.add(r)
            db.commit()

    # job 갱신
    j.status = InferenceJobStatus.DONE if not body.error else InferenceJobStatus.FAILED
    j.completed_at = utcnow_naive()
    j.decision = DecisionState(dec)
    j.run_id = run.run_id
    j.result_json = body.result_json or {}
    j.error = body.error

    db.commit()
    db.refresh(j)
    return j

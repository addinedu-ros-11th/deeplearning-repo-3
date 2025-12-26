# from datetime import datetime, timezone, timedelta
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.api.deps import get_db
# from app.core.security import require_admin_key
# from app.db.models import TraySession, RecognitionRun, DecisionState, Review, ReviewStatus, Store, Device, CctvEvent, CctvEventClip, CctvEventType, CctvEventStatus, DeviceType
# from app.schemas.inference import InferTrayRequest, InferTrayResponse, CctvInferRequest, CctvInferResponse
# from app.services.ai_client import AIClient, AIClientError
# from sqlalchemy import text
# from app.db.models import (
#     TraySessionStatus, OrderHdr, OrderLine, OrderStatus, MenuItem
# )

# router = APIRouter(dependencies=[Depends(require_admin_key)])

# def utcnow():
#     return datetime.now(timezone.utc).replace(tzinfo=None)

# TRAY_TIMEOUT_SEC = 30
# OVERLAP_BLOCK_THRESHOLD_DEFAULT = 0.25

# def _set_enum_or_str(obj, field: str, enum_value):
#     # 컬럼이 Enum 타입이든 str 타입이든 모두 안전하게 할당
#     try:
#         setattr(obj, field, enum_value)
#     except Exception:
#         setattr(obj, field, getattr(enum_value, "value", str(enum_value)))

# def _get_overlap_threshold_for_session(db: Session, s: TraySession) -> float:
#     try:
#         dv = db.query(Device).filter(Device.device_id == s.checkout_device_id).first()
#         cfg = (dv.config_json or {}) if dv else {}
#         gating = cfg.get("gating") or {}
#         v = gating.get("overlap_block_threshold")
#         if v is None:
#             return OVERLAP_BLOCK_THRESHOLD_DEFAULT
#         return float(v)
#     except Exception:
#         return OVERLAP_BLOCK_THRESHOLD_DEFAULT

# def _extract_order_items(result_json: dict) -> dict[int, int]:
#     """
#     AI result_json에서 item_id/qty를 최대한 유연하게 파싱.
#     기대 포맷(권장):
#       result_json.items = [{ "item_id": 101, "qty": 2 }, ...]
#     또는:
#       result_json.instances = [{ "best_item_id": 101, "qty": 2 }, ...]
#     반환: {item_id: total_qty}
#     """
#     items = result_json.get("items") or result_json.get("instances") or []
#     out: dict[int, int] = {}
#     for it in items:
#         if not isinstance(it, dict):
#             continue
#         item_id = it.get("item_id") or it.get("best_item_id") or it.get("menu_item_id")
#         qty = it.get("qty") or it.get("count") or 1
#         if item_id is None:
#             continue
#         try:
#             item_id_i = int(item_id)
#             qty_i = int(qty)
#         except Exception:
#             continue
#         if qty_i <= 0:
#             continue
#         out[item_id_i] = out.get(item_id_i, 0) + qty_i
#     return out

# def _ensure_order_for_session(db: Session, s: TraySession, result_json: dict) -> OrderHdr:
#     """
#     AUTO일 때만 호출. 이미 주문이 있으면 기존 주문 반환.
#     주문은 서버가 menu_item.price_won을 기준으로 생성.
#     """
#     existing = db.query(OrderHdr).filter(OrderHdr.session_id == s.session_id).first()
#     if existing:
#         return existing

#     item_qty = _extract_order_items(result_json)
#     if not item_qty:
#         # AUTO인데도 품목이 없으면 안전상 REVIEW로 전환하는 게 맞지만
#         # 여기서는 호출부에서 처리하도록 예외를 던짐
#         raise ValueError("empty order items in result_json")

#     menu_rows = db.query(MenuItem).filter(MenuItem.item_id.in_(list(item_qty.keys()))).all()
#     price_map = {m.item_id: int(m.price_won) for m in menu_rows}

#     # 가격 매칭 안 되는 item_id가 있으면 안전상 결제 생성 금지
#     missing = [iid for iid in item_qty.keys() if iid not in price_map]
#     if missing:
#         raise ValueError(f"price not found for item_ids={missing}")

#     total = 0
#     now = utcnow()

#     order = OrderHdr(
#         store_id=s.store_id,
#         session_id=s.session_id,
#         total_amount_won=0,  # 아래에서 업데이트
#         status=OrderStatus.PAID,
#         created_at=now,
#     )
#     db.add(order)
#     db.flush()  # order.order_id 확보

#     for iid, qty in item_qty.items():
#         unit = price_map[iid]
#         line_amount = unit * qty
#         total += line_amount
#         db.add(
#             OrderLine(
#                 order_id=order.order_id,
#                 item_id=iid,
#                 qty=qty,
#                 unit_price_won=unit,
#                 line_amount_won=line_amount,
#             )
#         )

#     order.total_amount_won = total
#     return order

# @router.post("/tray-sessions/{session_uuid}/infer", response_model=InferTrayResponse)
# def infer_tray(session_uuid: str, body: InferTrayRequest, db: Session = Depends(get_db)):
#     s = db.query(TraySession).filter(TraySession.session_uuid == session_uuid).first()
#     if not s:
#         raise HTTPException(status_code=404, detail="session not found")

#     # 1) 세션 상태 가드
#     if str(getattr(s, "status")) != str(TraySessionStatus.ACTIVE):
#         raise HTTPException(status_code=400, detail=f"session not ACTIVE (status={s.status})")

#     # 2) TIMEOUT 강제(30초)
#     now = utcnow()
#     try:
#         if s.started_at and (now - s.started_at).total_seconds() > TRAY_TIMEOUT_SEC:
#             _set_enum_or_str(s, "status", TraySessionStatus.TIMEOUT)
#             s.ended_at = now
#             s.end_reason = "TIMEOUT"
#             db.add(s)
#             db.commit()
#             raise HTTPException(status_code=400, detail="session timeout")
#     except HTTPException:
#         raise
#     except Exception:
#         # started_at 파싱/타입 이슈가 있어도 데모는 진행
#         pass

#     # attempt 계산
#     last = (
#         db.query(RecognitionRun)
#         .filter(RecognitionRun.session_id == s.session_id)
#         .order_by(RecognitionRun.attempt_no.desc())
#         .first()
#     )
#     attempt_no = 1 if not last else (last.attempt_no + 1)
#     if attempt_no > s.attempt_limit:
#         raise HTTPException(status_code=400, detail="attempt limit exceeded (call admin/manual)")

#     payload = {
#         "session_uuid": session_uuid,
#         "attempt_no": attempt_no,
#         "store_code": body.store_code,
#         "device_code": body.device_code,
#         "frame_b64": body.frame_b64,
#         "frame_gcs_uri": body.frame_gcs_uri,
#     }

#     # 3) AI 호출
#     try:
#         ai = AIClient()
#         ai_resp = ai.infer_tray(payload, timeout_s=10.0)
#     except AIClientError as e:
#         raise HTTPException(status_code=502, detail=str(e))

#     decision = ai_resp.get("decision")
#     if decision not in ("AUTO", "REVIEW", "UNKNOWN"):
#         raise HTTPException(status_code=502, detail="invalid decision from AI")

#     overlap_score = ai_resp.get("overlap_score")
#     result_json = ai_resp.get("result_json", {}) or {}

#     # 4) OVERLAP 차단(리뷰 생성 금지, UI 안내만)
#     # - threshold는 device.config_json로 override 가능
#     try:
#         thr = _get_overlap_threshold_for_session(db, s)
#         if overlap_score is not None and float(overlap_score) >= float(thr):
#             # decision을 REVIEW로 내려 UI가 재배치 유도하게 함
#             decision = "REVIEW"
#             result_json["block_reason"] = "OVERLAP"
#             result_json["overlap_threshold"] = thr
#     except Exception:
#         # overlap 처리 실패해도 infer는 진행
#         pass

#     # 5) recognition_run 저장(항상 저장: 감사/디버깅)
#     run = RecognitionRun(
#         session_id=s.session_id,
#         attempt_no=attempt_no,
#         overlap_score=overlap_score,
#         decision=DecisionState(decision),
#         result_json=result_json,
#         created_at=now,
#     )
#     db.add(run)
#     db.commit()
#     db.refresh(run)

#     # 6) REVIEW/UNKNOWN 처리
#     # - OVERLAP(block_reason=OVERLAP)일 때는 review row를 만들지 않음
#     if decision in ("REVIEW", "UNKNOWN"):
#         if result_json.get("block_reason") != "OVERLAP":
#             open_review = (
#                 db.query(Review)
#                 .filter(Review.session_id == s.session_id, Review.status == ReviewStatus.OPEN)
#                 .first()
#             )
#             if not open_review:
#                 r = Review(
#                     session_id=s.session_id,
#                     run_id=run.run_id,
#                     status=ReviewStatus.OPEN,
#                     reason=decision,
#                     top_k_json=result_json.get("top_k"),
#                     confirmed_items_json=None,
#                     created_at=utcnow(),
#                 )
#                 db.add(r)
#                 db.commit()

#         return InferTrayResponse(
#             overlap_score=overlap_score,
#             decision=decision,
#             result_json=result_json,
#         )

#     # 7) AUTO 처리: 주문 자동 생성 + 세션 종료(PAID)
#     # - 이미 주문이 있으면 재생성하지 않음
#     try:
#         order = _ensure_order_for_session(db, s, result_json)
#         _set_enum_or_str(s, "status", TraySessionStatus.PAID)
#         s.ended_at = utcnow()
#         s.end_reason = "PAID"
#         db.add(s)
#         db.commit()

#         # UI 편의: result_json에 주문 요약 넣어줌(스키마 영향 없음: Any)
#         result_json["order"] = {
#             "order_id": order.order_id,
#             "total_amount_won": order.total_amount_won,
#         }

#         return InferTrayResponse(
#             overlap_score=overlap_score,
#             decision="AUTO",
#             result_json=result_json,
#         )
#     except Exception as e:
#         # AUTO인데 주문 생성이 실패하면 안전상 REVIEW로 강등 + 리뷰 생성
#         result_json["block_reason"] = "ORDER_CREATE_FAILED"
#         result_json["error"] = str(e)

#         # run은 이미 저장됨. 리뷰 생성(OPEN)로 전환
#         open_review = (
#             db.query(Review)
#             .filter(Review.session_id == s.session_id, Review.status == ReviewStatus.OPEN)
#             .first()
#         )
#         if not open_review:
#             r = Review(
#                 session_id=s.session_id,
#                 run_id=run.run_id,
#                 status=ReviewStatus.OPEN,
#                 reason="REVIEW",
#                 top_k_json=result_json.get("top_k"),
#                 confirmed_items_json=None,
#                 created_at=utcnow(),
#             )
#             db.add(r)
#             db.commit()

#         return InferTrayResponse(
#             overlap_score=overlap_score,
#             decision="REVIEW",
#             result_json=result_json,
#         )

# # @router.post("/tray-sessions/{session_uuid}/infer", response_model=InferTrayResponse)
# # def infer_tray(session_uuid: str, body: InferTrayRequest, db: Session = Depends(get_db)):
# #     s = db.query(TraySession).filter(TraySession.session_uuid == session_uuid).first()
# #     if not s:
# #         raise HTTPException(status_code=404, detail="session not found")

# #     last = (
# #         db.query(RecognitionRun)
# #         .filter(RecognitionRun.session_id == s.session_id)
# #         .order_by(RecognitionRun.attempt_no.desc())
# #         .first()
# #     )
# #     attempt_no = 1 if not last else (last.attempt_no + 1)
# #     if attempt_no > s.attempt_limit:
# #         raise HTTPException(status_code=400, detail="attempt limit exceeded")

# #     payload = body.model_dump()
# #     payload["session_uuid"] = session_uuid

# #     try:
# #         ai = AIClient()
# #         ai_resp = ai.infer_tray(payload, timeout_s=10.0)
# #     except AIClientError as e:
# #         raise HTTPException(status_code=502, detail=str(e))

# #     decision = ai_resp.get("decision")
# #     if decision not in ("AUTO", "REVIEW", "UNKNOWN"):
# #         raise HTTPException(status_code=502, detail="invalid decision from AI")

# #     run = RecognitionRun(
# #         session_id=s.session_id,
# #         attempt_no=attempt_no,
# #         overlap_score=ai_resp.get("overlap_score"),
# #         decision=DecisionState(decision),
# #         result_json=ai_resp.get("result_json", {}),
# #         created_at=utcnow(),
# #     )
# #     db.add(run)
# #     db.commit()
# #     db.refresh(run)

# #     if decision in ("REVIEW", "UNKNOWN"):
# #         open_review = db.query(Review).filter(Review.session_id == s.session_id, Review.status == ReviewStatus.OPEN).first()
# #         if not open_review:
# #             r = Review(
# #                 session_id=s.session_id,
# #                 run_id=run.run_id,
# #                 status=ReviewStatus.OPEN,
# #                 reason=decision,
# #                 top_k_json=ai_resp.get("result_json", {}).get("top_k"),
# #                 confirmed_items_json=None,
# #                 created_at=utcnow(),
# #             )
# #             db.add(r)
# #             db.commit()

# #     return InferTrayResponse(
# #         overlap_score=ai_resp.get("overlap_score"),
# #         decision=decision,
# #         result_json=ai_resp.get("result_json", {}),
# #     )

# @router.post("/cctv/infer", response_model=CctvInferResponse)
# def infer_cctv(body: CctvInferRequest, db: Session = Depends(get_db)):
#     # store/device lookup by code (safer for external caller)
#     if not body.store_code or not body.device_code:
#         raise HTTPException(status_code=400, detail="store_code and device_code required")

#     st = db.query(Store).filter(Store.store_code == body.store_code).first()
#     if not st:
#         raise HTTPException(status_code=404, detail="store not found")

#     dv = (
#         db.query(Device)
#         .filter(Device.store_id == st.store_id)
#         .filter(Device.device_code == body.device_code)
#         .filter(Device.device_type == DeviceType.CCTV)
#         .first()
#     )
#     if not dv:
#         raise HTTPException(status_code=404, detail="cctv device not found")

#     payload = body.model_dump()

#     try:
#         ai = AIClient()
#         ai_resp = ai.infer_cctv(payload, timeout_s=20.0)
#     except AIClientError as e:
#         raise HTTPException(status_code=502, detail=str(e))

#     events = ai_resp.get("events") or []
#     created = []

#     for ev in events:
#         et = ev.get("event_type")
#         conf = ev.get("confidence", 0.0)
#         started = ev.get("started_at")
#         ended = ev.get("ended_at")
#         meta = ev.get("meta_json") or ev.get("meta") or {}

#         if et not in ("VANDALISM", "VIOLENCE", "FALL", "WHEELCHAIR"):
#             # ignore unknown event types (demo-safe)
#             continue

#         try:
#             started_dt = datetime.fromisoformat(str(started).replace("Z", "").replace("T", " "))
#             ended_dt = datetime.fromisoformat(str(ended).replace("Z", "").replace("T", " "))
#         except Exception:
#             # if parsing fails, skip
#             continue

#         row = CctvEvent(
#             store_id=st.store_id,
#             cctv_device_id=dv.device_id,
#             event_type=CctvEventType(et),
#             confidence=conf,
#             status=CctvEventStatus.OPEN,
#             started_at=started_dt,
#             ended_at=ended_dt,
#             meta_json=meta,
#             created_at=utcnow(),
#         )
#         db.add(row)
#         db.commit()
#         db.refresh(row)

#         # optional clip row if request had a clip uri
#         if body.clip_gcs_uri:
#             clip = CctvEventClip(
#                 event_id=row.event_id,
#                 clip_gcs_uri=body.clip_gcs_uri,
#                 clip_start_at=(started_dt - timedelta(seconds=3)),
#                 clip_end_at=(ended_dt + timedelta(seconds=5)),
#                 created_at=utcnow(),
#             )
#             db.add(clip)
#             db.commit()

#         created.append({"event_id": row.event_id, "event_type": et})

#     return CctvInferResponse(events=events)

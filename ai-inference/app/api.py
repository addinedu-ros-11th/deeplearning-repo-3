from fastapi import APIRouter, Depends
from app.core.security import require_ai_key
from app.schemas import TrayInferRequest, TrayInferResponse, CctvInferRequest, CctvInferResponse
from app.services.engine import InferenceEngine

router = APIRouter(dependencies=[Depends(require_ai_key)])
engine = InferenceEngine()

@router.get("/health")
def health():
    return {"ok": True}

@router.post("/infer/tray", response_model=TrayInferResponse)
def infer_tray(body: TrayInferRequest):
    return TrayInferResponse(**engine.infer_tray(body.model_dump()))

@router.post("/infer/cctv", response_model=CctvInferResponse)
def infer_cctv(body: CctvInferRequest):
    return CctvInferResponse(**engine.infer_cctv(body.model_dump()))

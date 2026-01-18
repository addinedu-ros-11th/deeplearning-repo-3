from fastapi import APIRouter, Depends, HTTPException
from app.core.security import require_admin_key
from app.services.stream_sender import get_stream_manager
from app.schemas.stream import (
    StreamStartRequest,
    StreamStartResponse,
    StreamStopRequest,
    StreamStopResponse,
    StreamInfo,
    StreamListResponse,
)

router = APIRouter(prefix="/streams", dependencies=[Depends(require_admin_key)])


@router.post("/start", response_model=StreamStartResponse)
def start_stream(req: StreamStartRequest):
    manager = get_stream_manager()

    try:
        session_id = manager.start_stream(
            store_code=req.store_code,
            device_code=req.device_code,
            rtsp_uri=req.rtsp_uri,
            target_host=req.target_host,
            target_port=req.target_port,
            fps=req.fps,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스트리밍 시작 실패: {e}")

    session_info = manager.get_stream(session_id)
    if not session_info:
        raise HTTPException(status_code=500, detail="세션 생성 후 조회 실패")

    return StreamStartResponse(
        session_id=session_info["session_id"],
        store_code=session_info["store_code"],
        device_code=session_info["device_code"],
        rtsp_uri=session_info["rtsp_uri"],
        target_host=session_info["target_host"],
        target_port=session_info["target_port"],
        fps=session_info["fps"],
    )


@router.post("/stop", response_model=StreamStopResponse)
def stop_stream(req: StreamStopRequest):
    manager = get_stream_manager()

    if req.session_id:
        success = manager.stop_stream(req.session_id)
        if success:
            return StreamStopResponse(
                success=True,
                session_id=req.session_id,
                message="스트리밍이 중지되었습니다.",
            )
        else:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    if req.store_code and req.device_code:
        success = manager.stop_stream_by_device(req.store_code, req.device_code)
        if success:
            return StreamStopResponse(
                success=True,
                message=f"스트리밍이 중지되었습니다: {req.store_code}/{req.device_code}",
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"세션을 찾을 수 없습니다: {req.store_code}/{req.device_code}",
            )

    raise HTTPException(
        status_code=400,
        detail="session_id 또는 store_code/device_code를 지정해야 합니다.",
    )


@router.get("", response_model=StreamListResponse)
def list_streams():
    manager = get_stream_manager()
    streams = manager.list_streams()

    return StreamListResponse(
        streams=[StreamInfo(**s) for s in streams],
        total=len(streams),
    )


@router.get("/{session_id}", response_model=StreamInfo)
def get_stream(session_id: str):
    manager = get_stream_manager()
    session_info = manager.get_stream(session_id)

    if not session_info:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    return StreamInfo(**session_info)


@router.post("/stop-all")
def stop_all_streams():
    manager = get_stream_manager()
    count = manager.stop_all()

    return {
        "success": True,
        "stopped_count": count,
        "message": f"{count}개의 스트리밍 세션이 중지되었습니다.",
    }

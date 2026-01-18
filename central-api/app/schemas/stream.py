from pydantic import BaseModel, Field
from typing import Optional


class StreamStartRequest(BaseModel):
    store_code: str = Field(..., description="매장 코드")
    device_code: str = Field(..., description="디바이스 코드")
    rtsp_uri: str = Field(..., description="RTSP 스트림 URI")
    target_host: Optional[str] = Field(None, description="AI 서버 IP (기본값: 설정값 사용)")
    target_port: Optional[int] = Field(None, description="AI 서버 UDP 포트 (기본값: 5005)")
    fps: Optional[int] = Field(None, ge=1, le=30, description="프레임 전송 FPS (기본값: 15)")


class StreamStartResponse(BaseModel):
    session_id: str
    store_code: str
    device_code: str
    rtsp_uri: str
    target_host: str
    target_port: int
    fps: int


class StreamStopRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="세션 ID")
    store_code: Optional[str] = Field(None, description="매장 코드 (session_id 없을 때 사용)")
    device_code: Optional[str] = Field(None, description="디바이스 코드 (session_id 없을 때 사용)")


class StreamStopResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    message: str


class StreamInfo(BaseModel):
    session_id: str
    rtsp_uri: str
    store_code: str
    device_code: str
    target_host: str
    target_port: int
    fps: int
    running: bool
    frame_index: int


class StreamListResponse(BaseModel):
    streams: list[StreamInfo]
    total: int

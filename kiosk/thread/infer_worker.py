from PyQt6.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv
import requests
import base64
import os

load_dotenv()


class InferWorker(QThread):
    """AI 추론 API를 호출하는 Worker 스레드"""
    success = pyqtSignal(dict)  # AI 추론 결과 전달
    error = pyqtSignal(str)

    def __init__(self, session_uuid: str, frame_bytes: bytes, store_code: str = None, device_code: str = None):
        """
        Args:
            session_uuid: 트레이 세션 UUID
            frame_bytes: 웹캠에서 캡처한 이미지 바이트 (JPEG/PNG)
            store_code: 매장 코드 (옵션)
            device_code: 체크아웃 디바이스 코드 (옵션)
        """
        super().__init__()
        self.api_url = os.getenv("API_URL") + f"/api/v1/tray-sessions/{session_uuid}/infer"
        self.frame_bytes = frame_bytes
        self.store_code = store_code
        self.device_code = device_code
        self.headers = {"Content-Type": "application/json"}
        admin_key = os.getenv("ADMIN_KEY")
        if admin_key:
            self.headers["X-ADMIN-KEY"] = admin_key

    def run(self):
        try:
            # 이미지를 base64로 인코딩
            frame_b64 = base64.b64encode(self.frame_bytes).decode("utf-8")

            # 요청 데이터 구성
            payload = {
                "frame_b64": frame_b64,
            }
            if self.store_code:
                payload["store_code"] = self.store_code
            if self.device_code:
                payload["device_code"] = self.device_code

            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=15  # AI 추론은 시간이 더 걸릴 수 있음
            )

            if 200 <= response.status_code < 300:
                result = response.json()
                self.success.emit(result)
            else:
                error_detail = response.json().get("detail", "Unknown error")
                self.error.emit(f"AI 추론 실패 ({response.status_code}): {error_detail}")

        except requests.exceptions.Timeout:
            self.error.emit("AI 추론 시간 초과 (15초)")
        except requests.exceptions.ConnectionError:
            self.error.emit("서버 연결 실패 - 네트워크를 확인하세요")
        except Exception as e:
            self.error.emit(f"AI 추론 오류: {str(e)}")

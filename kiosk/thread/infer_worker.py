from PyQt6.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv
import requests
import base64
import os
import time

load_dotenv()


class InferWorker(QThread):
    """AI 추론 Job Queue 방식 Worker 스레드"""
    success = pyqtSignal(dict)  # AI 추론 결과 전달
    error = pyqtSignal(str)

    def __init__(self, session_uuid: str, frame_bytes: bytes, store_code: str = None, device_code: str = None):
        """
        Args:
            session_uuid: 트레이 세션 UUID
            frame_bytes: 웹캠에서 캡처한 이미지 바이트 (JPEG/PNG)
            store_code: 매장 코드
            device_code: 체크아웃 디바이스 코드
        """
        super().__init__()
        self.base_url = os.getenv("API_URL")
        self.frame_bytes = frame_bytes
        self.session_uuid = session_uuid
        self.store_code = store_code
        self.device_code = device_code
        self.headers = {"Content-Type": "application/json"}
        admin_key = os.getenv("ADMIN_KEY")
        if admin_key:
            self.headers["X-ADMIN-KEY"] = admin_key

        # Polling 설정
        self.poll_interval = 0.5  # 0.5초마다 polling
        self.max_wait_time = 30   # 최대 30초 대기

    def run(self):
        try:
            # 1. Job 생성
            job_id = self._create_job()
            if not job_id:
                return

            # 2. Job 완료 대기 (polling)
            result = self._wait_for_completion(job_id)
            if result:
                self.success.emit(result)

        except requests.exceptions.Timeout:
            self.error.emit("AI 추론 시간 초과")
        except requests.exceptions.ConnectionError:
            self.error.emit("서버 연결 실패 - 네트워크를 확인하세요")
        except Exception as e:
            self.error.emit(f"AI 추론 오류: {str(e)}")

    def _create_job(self) -> int | None:
        """Job 생성 요청"""
        url = f"{self.base_url}/api/v1/inference/tray/jobs"

        # 이미지를 base64로 인코딩
        frame_b64 = base64.b64encode(self.frame_bytes).decode("utf-8")

        payload = {
            "session_uuid": self.session_uuid,
            "frame_b64": frame_b64,
            "store_code": self.store_code,
            "device_code": self.device_code,
        }

        response = requests.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=10
        )

        if 200 <= response.status_code < 300:
            result = response.json()
            job_id = result.get("job_id")
            return job_id
        else:
            error_detail = response.json().get("detail", "Unknown error")
            self.error.emit(f"Job 생성 실패 ({response.status_code}): {error_detail}")
            return None

    def _wait_for_completion(self, job_id: int) -> dict | None:
        """Job 완료 대기 (polling)"""
        url = f"{self.base_url}/api/v1/inference/tray/jobs/{job_id}"
        elapsed = 0

        while elapsed < self.max_wait_time:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=5
            )

            if response.status_code != 200:
                self.error.emit(f"Job 조회 실패 ({response.status_code})")
                return None

            job = response.json()
            status = job.get("status")

            if status == "DONE":
                # 완료 - 결과 반환
                return {
                    "decision": job.get("decision"),
                    "overlap_score": job.get("overlap_score"),
                    "result_json": job.get("result_json") or {},
                }
            elif status == "FAILED":
                # 실패
                error_msg = job.get("error") or "AI 추론 실패"
                self.error.emit(error_msg)
                return None

            # PENDING 또는 CLAIMED - 계속 대기
            time.sleep(self.poll_interval)
            elapsed += self.poll_interval

        # 타임아웃
        self.error.emit(f"AI 추론 시간 초과 ({self.max_wait_time}초)")
        return None

from PyQt6.QtCore import QThread, pyqtSignal
import requests
from dotenv import load_dotenv
import os

load_dotenv()

class APIWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    success = pyqtSignal(dict)
    
    def __init__(self, api_url, method="GET", data=None, headers=None):
        """서버의 API를 비동기로 호출하는 스레드"""
        super().__init__()
        self.api_url = os.getenv("API_URL") + api_url
        self.method = method.upper()
        self.data = data
        self.headers = headers or {}
        
    def run(self):
        """스레드에서 실행될 코드"""
        try:
            if self.method == "GET":
                response = requests.get(
                    self.api_url, 
                    headers=self.headers, 
                    timeout=10
                )
            elif self.method == "POST":
                response = requests.post(
                    self.api_url, 
                    json=self.data, 
                    headers=self.headers, 
                    timeout=10
                )
            elif self.method == "PUT":
                response = requests.put(
                    self.api_url, 
                    json=self.data, 
                    headers=self.headers, 
                    timeout=10
                )
            elif self.method == "DELETE":
                response = requests.delete(
                    self.api_url, 
                    headers=self.headers, 
                    timeout=10
                )
            else:
                self.error.emit(f"지원하지 않는 HTTP 메서드: {self.method}")
                return
            
            # 상태 코드 확인 (200번대 모두 성공 처리)
            if 200 <= response.status_code < 300:
                try:
                    self.success.emit(response.json())
                except ValueError:
                    # JSON 파싱 실패 시 빈 dict 전달
                    self.success.emit({})
            else:
                # 에러 응답에 detail이 있으면 포함
                try:
                    error_detail = response.json().get("detail", "")
                    self.error.emit(f"HTTP {response.status_code}: {error_detail}")
                except:
                    self.error.emit(f"HTTP Error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.error.emit("요청 시간 초과 (10초)")
        except requests.exceptions.ConnectionError:
            self.error.emit("서버 연결 실패 - 네트워크를 확인하세요")
        except Exception as e:
            self.error.emit(f"알 수 없는 오류: {str(e)}")
        finally:
            self.finished.emit()
from PyQt6.QtCore import QThread, pyqtSignal
import requests

class OrderSaveWorker(QThread):
    success = pyqtSignal(dict)  # 서버 응답 전달
    error = pyqtSignal(str)
    
    def __init__(self, api_url, order_data):
        """주문 저장을 서버에 요청하는 스레드"""
        super().__init__()
        self.api_url = api_url
        self.order_data = order_data
    
    def run(self):
        try:
            response = requests.post(
                self.api_url,
                json=self.order_data,
                timeout=10
            )
            
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                self.success.emit(result)  # order_id 등 반환값 전달
            else:
                error_detail = response.json().get("detail", "Unknown error")
                self.error.emit(f"서버 오류 ({response.status_code}): {error_detail}")
                
        except requests.exceptions.RequestException as e:
            self.error.emit(f"네트워크 오류: {str(e)}")
        except Exception as e:
            self.error.emit(f"주문 저장 실패: {str(e)}")
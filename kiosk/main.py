from PyQt6.QtWidgets import (QApplication, QMainWindow, QStackedWidget)
from PyQt6.QtCore import QTimer
from thread.server_worker import APIWorker
import logging

from model.cart_data import CartData
from ui.home_screen import HomeScreen
from ui.scan_screen import ScanScreen
from ui.payment_screen import PaymentScreen
from ui.check_screen import CheckScreen


class KioskApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("키오스크")
        self.setGeometry(100, 100, 1080, 1920)
        self.setStyleSheet("background-color: #FAF3E1;")

        self.store_id = 1
        self.device_id = 1
        
        # 스택 위젯 생성
        self.stacked = QStackedWidget()
        
        # 장바구니 데이터 모델 생성
        self.data = CartData()

        # 각 화면 생성
        self.home_screen = HomeScreen(self.switch_screen)
        self.scan_screen = ScanScreen(self.switch_screen, self.data, self.store_id, self.device_id)
        self.check_screen = CheckScreen(self.switch_screen, self.data)
        self.payment_screen = PaymentScreen(self.switch_screen, self.data)
        
        # 스택에 추가
        self.stacked.addWidget(self.home_screen)      # index 0
        self.stacked.addWidget(self.scan_screen)   # index 1
        self.stacked.addWidget(self.check_screen)   # index 2
        self.stacked.addWidget(self.payment_screen)   # index 3
        
        # 홈 화면 표시
        self.stacked.setCurrentIndex(0)

        self.setCentralWidget(self.stacked)

        # 서버 헬스체크 폴링 설정
        self.is_server_connected = False
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self.check_server_health)
        self.health_check_timer.start(10000)  # 10초마다 체크

        # 초기 헬스체크 실행
        self.check_server_health()

    def check_server_health(self):
        """서버 연결 상태 확인"""
        self.health_worker = APIWorker(
            api_url="/health",
            method="GET"
        )
        self.health_worker.success.connect(self.on_health_check_success)
        self.health_worker.error.connect(self.on_health_check_error)
        self.health_worker.start()

    def on_health_check_success(self, result):
        """서버 연결 성공"""
        if not self.is_server_connected:
            logging.info("[헬스체크] 서버 연결됨")
        self.is_server_connected = True

    def on_health_check_error(self, error_msg):
        """서버 연결 실패"""
        if self.is_server_connected:
            logging.warning(f"[헬스체크] 서버 연결 끊김: {error_msg}")
        self.is_server_connected = False
    
    def switch_screen(self, screen_name):
        """상태에 따라 화면 전환"""
        screens = {
            'home': 0,
            'scan': 1,
            'check': 2,
            'payment': 3
        }

        if screen_name in screens:
            # check 화면 전환 시 장바구니 데이터로 UI 갱신
            if screen_name == 'check':
                self.check_screen.refresh()
            self.stacked.setCurrentIndex(screens[screen_name])


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = KioskApp()
    window.show()
    sys.exit(app.exec())
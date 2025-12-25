from PyQt6.QtWidgets import (QApplication, QMainWindow, QStackedWidget)

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
    
    def switch_screen(self, screen_name):
        """상태에 따라 화면 전환"""
        screens = {
            'home': 0,
            'scan': 1,
            'check': 2,
            'payment': 3
        }
        
        if screen_name in screens:
            self.stacked.setCurrentIndex(screens[screen_name])


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = KioskApp()
    window.show()
    sys.exit(app.exec())
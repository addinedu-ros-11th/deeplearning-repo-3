from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
from popup.payment_popup import PaymentTimeoutPopup, PaymentCompletePopup
from time import time

class PaymentScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.is_payed = False
        self.timer_started = False
        self.timeout_timer = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        status_bar = QLabel("스캔")
        status_bar.setStyleSheet("""
            background-color: rgba(255, 109, 31, 0.7);
            color: #222222;
            font-size: 80pt;
            font-weight: bold;
            padding: 20px;
        """)
        status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_bar.setFixedHeight(150)
        layout.addWidget(status_bar)

        layout.addSpacing(400)
        title = QLabel("카드를 태그해 주세요!")
        title.setStyleSheet("font-size: 48px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        image = QLabel()
        pixmap = QPixmap('./data/payment.png')
        scaled_pixmap = pixmap.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image.setPixmap(scaled_pixmap)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        self.setLayout(layout)
    
    def showEvent(self, event):
        """화면이 표시될 때 timer 관련 변수 초기화"""
        super().showEvent(event)
        if not self.timer_started:
            self.timer_started = True
            self.start_timeout_timer()
            
            # 테스트용
            #self.on_payment_success()
    
    def start_timeout_timer(self):
        """5초 후 타임아웃 체크"""
        print("타이머 시작!")
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.check_payment_status)
        self.timeout_timer.start(5000)  # 5초
    
    def check_payment_status(self):
        """결제 상태 확인"""
        print("타임아웃 체크!")
        self.timeout_timer.stop()
        
        if not self.is_payed:
            timeout_popup = PaymentTimeoutPopup()
            timeout_popup.exec()
            
            if timeout_popup.result == 'home':
                self.switch_callback('home')
            elif timeout_popup.result == 'retry':
                # 재시도 - 타이머 재시작
                self.timer_started = False
                self.start_timeout_timer()
        else:
            # 결제 완료
            complete_popup = PaymentCompletePopup()
            complete_popup.exec()
            
            if complete_popup.result == 'home':
                self.switch_callback('home')
    
    def on_payment_success(self):
        """RFID 결제 성공 시 호출할 메서드"""
        print("결제 성공!")
        self.is_payed = True
        
        # 타이머가 있고 실행 중이면 중지
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()
        
        complete_popup = PaymentCompletePopup()
        complete_popup.exec()
        
        if complete_popup.result == 'home':
            self.switch_callback('home')

# 테스트 코드
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    
    def dummy_callback(screen):
        print(f"Callback called: {screen}")
    
    window = PaymentScreen(dummy_callback)
    window.show()
    
    sys.exit(app.exec())
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PyQt6.QtWidgets import QGraphicsOpacityEffect
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
        
        # status bar 영역
        status_bar = QLabel("결제")
        status_bar.setStyleSheet("""
            background-color: rgba(255, 109, 31, 0.7);
            color: #222222;
            font-size: 80pt;
            padding: 20px;
        """)
        status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_bar.setFixedHeight(150)
        layout.addWidget(status_bar)

        # 글 영역
        layout.addSpacing(400)
        title = QLabel("카드를 태그해 주세요!")
        title.setStyleSheet("font-size: 48px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        # 이미지 영역
        self.image = QLabel()
        pixmap = QPixmap('./data/payment.png')
        scaled_pixmap = pixmap.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image.setPixmap(scaled_pixmap)
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setup_blink_animation()

        layout.addStretch()

        self.setLayout(layout)

    def setup_blink_animation(self):
        """이미지 깜빡임 애니메이션"""
        effect = QGraphicsOpacityEffect(self.image)
        self.image.setGraphicsEffect(effect)

        self.blink_anim = QPropertyAnimation(effect, b"opacity")
        self.blink_anim.setDuration(1500)
        self.blink_anim.setStartValue(1.0)
        self.blink_anim.setEndValue(0.3)
        self.blink_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.blink_anim.finished.connect(self.toggle_blink_direction)

        self.blink_anim.start()

    def toggle_blink_direction(self):
        """깜빡임 무한 반복을 위한 토글"""
        if self.blink_anim.direction() == QAbstractAnimation.Direction.Forward:
            self.blink_anim.setDirection(QAbstractAnimation.Direction.Backward)
        else:
            self.blink_anim.setDirection(QAbstractAnimation.Direction.Forward)

        self.blink_anim.start()

    
    def showEvent(self, event):
        """화면이 표시될 때 timer 관련 변수 초기화"""
        super().showEvent(event)
        if not self.timer_started:
            self.timer_started = True
            self.start_timeout_timer()

    def start_timeout_timer(self):
        """5초 후 타임아웃 체크"""
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.check_payment_status)
        self.timeout_timer.start(5000)
    
    def check_payment_status(self):
        """결제 상태 확인"""
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
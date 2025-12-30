from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from popup.payment_popup import PaymentTimeoutPopup, PaymentCompletePopup
from time import time
from datetime import datetime
from thread.order_save_worker import OrderSaveWorker
import logging
from arduino.check_pay import RFIDPayment

class PaymentScreen(QWidget):
    def __init__(self, switch_callback, data):
        super().__init__()
        self.switch_callback = switch_callback
        self.is_payed = False
        self.timer_started = False
        self.timeout_timer = None
        self.data = data
        self.init_ui()
        self.payment_class = RFIDPayment()
    
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
        self.is_payed = self.payment_class.check_pay()
        
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
            self.on_payment_success()
    
    def on_payment_success(self):
        """RFID 결제 성공 시 호출할 메서드"""
        self.is_payed = True

        # 타이머가 있고 실행 중이면 중지
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()

        # 주문 정보를 서버에 저장
        self.save_order_to_server()

    def save_order_to_server(self):
        """장바구니 아이템을 서버에 저장"""
        
        # OrderLine 형식으로 변환
        lines = []
        item_names = self.data.get_item_name()  # 리스트라고 가정
        item_quantities = self.data.get_item_quantity()  # 리스트라고 가정
        
        # 각 아이템을 OrderLine 형식으로 변환
        for i, (name, qty) in enumerate(zip(item_names, item_quantities)):
            lines.append({
                "item_id": self.data.get_item_ids()[i],
                "qty": qty,
                "unit_price_won": self.data.get_unit_prices()[i],
                "line_amount_won": self.data.get_unit_prices()[i] * qty
            })
        
        order_data = {
            "store_id": self.data.get_store_id(),
            "session_id": self.data.get_session_id(),
            "total_amount_won": self.data.get_total_amount(),
            "lines": lines
        }

        logging.info(f"[TEST] 주문 데이터: {order_data}")
        self.order_worker = OrderSaveWorker(
            api_url="/api/v1/orders/save",
            order_data=order_data
        )
        
        # 신호 연결
        self.order_worker.success.connect(self.on_order_save_success)
        self.order_worker.error.connect(self.on_order_save_error)
        
        logging.info("[TEST] OrderSaveWorker 스레드 시작")
        self.order_worker.start()

    def on_order_save_success(self, result):
        """주문 저장 성공"""
        logging.info(f"[주문저장] 주문 저장 성공: {result}")

        # 장바구니 초기화
        self.data.clear()

        # 결제 완료 팝업 표시
        complete_popup = PaymentCompletePopup()
        complete_popup.exec()

        if complete_popup.result == 'home':
            self.switch_callback('home')

    def on_order_save_error(self, error_msg):
        """주문 저장 실패"""
        logging.error(f"[주문저장] 주문 저장 실패: {error_msg}")

        complete_popup = PaymentCompletePopup()
        complete_popup.exec()

        if complete_popup.result == 'home':
            self.switch_callback('home')

# 테스트 코드
if __name__ == '__main__':
    import sys
    from model.cart_data import CartData
    app = QApplication(sys.argv)

    def dummy_callback(screen):
        print(f"Callback called: {screen}")

    dummy_data = CartData()
    window = PaymentScreen(dummy_callback, dummy_data)
    window.show()

    sys.exit(app.exec())
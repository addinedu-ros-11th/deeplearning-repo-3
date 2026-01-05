from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea)
from PyQt6.QtCore import Qt
from thread.server_worker import APIWorker
from popup.call_popup import CallFailPopup, CallSuccessPopup
import logging

class CheckScreen(QWidget):
    def __init__(self, switch_callback, data):
        super().__init__()
        self.switch_callback = switch_callback
        self.data = data
        self.init_ui()
    
    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.setLayout(self.main_layout)
        self.refresh()

    def refresh(self):
        """장바구니 데이터로 UI 갱신"""
        # 기존 위젯 제거
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        layout = self.main_layout

        # 장바구니 데이터에서 총 수량, 총액 계산
        total_qty = sum(item["qty"] for item in self.data.items) if self.data.items else 0
        total_amount = self.data.get_total_amount() if self.data.items else 0
        
        # status bar 영역
        status_bar = QLabel("주문 내역 확인")
        status_bar.setStyleSheet("""
            background-color: rgba(255, 109, 31, 0.7);
            color: #222222;
            font-size: 80pt;
            padding: 20px;
        """)
        status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_bar.setFixedHeight(150)
        layout.addWidget(status_bar)
        layout.addSpacing(40)

        container = QWidget()
        container.setFixedSize(1018, 1000)
        container.setStyleSheet("""
            QWidget {
                background-color: #F5E7C6;
                border-radius: 30px;
            }
        """)
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # 스크롤 영역
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedSize(1018, 1000)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #F5E7C6;
                border: none;
                border-top-left-radius: 30px;
                border-top-right-radius: 30px;
                padding-top: 10px;
                padding-right: 10px;

            }
            QScrollBar:vertical {
                background-color: #F5E7C6;
                width: 10px;
                margin: 30px 5px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 109, 31, 0.5);
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("""
                background-color: transparent;
                border: none;
                """)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_layout.setSpacing(7)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        # 장바구니 아이템 리스트
        for cart_item in self.data.items:
            item_name = cart_item.get("name", "알 수 없음")
            item_qty = cart_item.get("qty", 1)
            item_price = cart_item.get("unit_price", 0)

            item_container = QWidget()
            item_container.setFixedSize(955, 100)
            item_container.setStyleSheet("""
                background-color: rgba(250, 243, 225, 0.7);
                border-radius: 10px;
            """)

            item_layout = QHBoxLayout(item_container)
            item_layout.setContentsMargins(30, 15, 30, 15)

            # 이름 (왼쪽)
            name_label = QLabel(item_name)
            name_label.setStyleSheet("font-size: 36px; background: transparent;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            # 단가 x 개수 (오른쪽)
            price_label = QLabel(f"{item_price:,}원 x {item_qty}")
            price_label.setStyleSheet("font-size: 36px; background: transparent;")
            price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            item_layout.addWidget(name_label)
            item_layout.addWidget(price_label)

            self.scroll_layout.addSpacing(10)
            self.scroll_layout.addWidget(item_container)
        
        self.scroll_layout.addStretch()
        scroll_area.setWidget(self.scroll_content)
        container_layout.addWidget(scroll_area, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(100)

        # 총 수량, 총액 영역
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(50, 10, 50, 10)
        label_layout.setSpacing(0)
        label_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(100)

        total_qty_label = QLabel("총 수량")
        total_qty_label.setStyleSheet("""
            color: #222222;
            font-size: 30pt;
        """)
        total_qty_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(total_qty_label)

        total_amount_label = QLabel("총액")
        total_amount_label.setStyleSheet("""
            color: #222222;
            font-size: 30pt;
        """)
        total_amount_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(total_amount_label)

        label_layout.addLayout(left_layout, 1)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(100)

        total_qty_value_label = QLabel(f"{total_qty}개")
        total_qty_value_label.setStyleSheet("""
            color: #222222;
            font-size: 30pt;
        """)
        total_qty_value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(total_qty_value_label)

        total_amount_value_label = QLabel(f"{total_amount:,}원")
        total_amount_value_label.setStyleSheet("""
            color: #222222;
            font-size: 30pt;
        """)
        total_amount_value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(total_amount_value_label)

        label_layout.addLayout(right_layout, 1)

        layout.addLayout(label_layout)

        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.setSpacing(100)
        button_layout.setContentsMargins(20, 0, 20, 100)
        
        call_btn = QPushButton("관리자 호출")
        call_btn.setStyleSheet("""
            QPushButton {
                font-size: 40px;
                padding: 15px;
                background-color: #E6DABD;
                color: white;
                border: none;
                border-radius: 30px;
            }
            QPushButton:hover {
                background-color: rgba(230, 218, 189, 0.5);
            }
        """)
        call_btn.clicked.connect(self.call_admin)
        
        pay_btn = QPushButton("결제")
        pay_btn.setStyleSheet("""
            QPushButton {
                font-size: 40px;
                padding: 15px;
                background-color: #FF6D1F;
                color: white;
                border: none;
                border-radius: 30px;
            }
            QPushButton:hover {
                background-color: #E55A0F;
            }
        """)
        pay_btn.clicked.connect(lambda: self.switch_callback('payment'))
        
        button_layout.addWidget(call_btn)
        button_layout.addWidget(pay_btn)
        
        layout.addStretch()
        layout.addSpacing(40)
        layout.addLayout(button_layout)

    def _clear_layout(self, layout):
        """레이아웃 내 모든 위젯 제거"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def call_admin(self):
        """관리자 호출 - 서버에 리뷰 생성 요청"""
        session_id = self.data.get_session_id()
        if not session_id:
            logging.warning("[관리자호출] 세션 ID가 없습니다")
            return

        review_data = {
            "session_id": session_id,
            "reason": "ADMIN_CALL"
        }

        self.admin_call_worker = APIWorker(
            api_url="/api/v1/reviews",
            method="POST",
            data=review_data
        )
        self.admin_call_worker.success.connect(self.on_admin_call_success)
        self.admin_call_worker.error.connect(self.on_admin_call_error)
        self.admin_call_worker.start()

        logging.info(f"[관리자호출] 요청 전송: session_id={session_id}")

    def on_admin_call_success(self, result):
        """관리자 호출 성공"""
        logging.info(f"[관리자호출] 성공: {result}")
        call_success_popup = CallSuccessPopup()
        call_success_popup.exec()

        if call_success_popup.result == 'home':
            self.switch_callback('home')

    def on_admin_call_error(self, error_msg):
        """관리자 호출 실패"""
        logging.error(f"[관리자호출] 실패: {error_msg}")
        call_fail_popup = CallFailPopup()
        call_fail_popup.exec()

        if call_fail_popup.result == 'home':
            self.switch_callback('home')
        elif call_fail_popup.result == 'retry':
            self.switch_callback('scan')

    def complete_payment(self):
        print("결제 완료!")
        self.switch_callback('home')

if __name__ == '__main__':
    import sys
    from model.cart_data import CartData
    app = QApplication(sys.argv)

    def dummy_callback(screen):
        print(f"Callback called: {screen}")

    # 테스트용 장바구니 데이터
    dummy_data = CartData()
    dummy_data.items = [
        {"item_id": 1, "name": "아메리카노", "qty": 2, "unit_price": 4500},
        {"item_id": 2, "name": "카페라떼", "qty": 1, "unit_price": 5000},
        {"item_id": 3, "name": "치즈케이크", "qty": 1, "unit_price": 6500},
    ]

    window = CheckScreen(dummy_callback, dummy_data)
    window.show()

    sys.exit(app.exec())
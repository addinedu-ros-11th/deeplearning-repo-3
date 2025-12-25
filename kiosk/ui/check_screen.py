from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea)
from PyQt6.QtCore import Qt

class CheckScreen(QWidget):
    def __init__(self, switch_callback, data):
        super().__init__()
        self.switch_callback = switch_callback
        self.data = data
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()

        self.total_qty_value_contents = "100"
        self.total_amount_value_contents = "10,000"

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
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
        
        # 임시 아이템 리스트
        for i in range(10):
            item = QLabel(f"아이템 {i+1}")
            item.setFixedSize(955, 170)
            item.setStyleSheet("""
                background-color: rgba(250, 243, 225, 0.7);
                border-radius: 3px;
                font-size: 16px;
                padding: 7px;
            """)
            item.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.scroll_layout.addSpacing(10)
            self.scroll_layout.addWidget(item)
        
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

        self.total_qty_value_contents = "100"
        right_layout = QVBoxLayout()
        right_layout.setSpacing(100)

        total_qty_value = QLabel(self.total_qty_value_contents)
        total_qty_value.setStyleSheet("""
            color: #222222;
            font-size: 30pt;
        """)
        total_qty_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(total_qty_value)

        total_amount_value = QLabel(self.total_amount_value_contents)
        total_amount_value.setStyleSheet("""
            color: #222222;
            font-size: 30pt;
        """)
        total_amount_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(total_amount_value)

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
        call_btn.clicked.connect(lambda: self.switch_callback('scan'))
        
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
        
        self.setLayout(layout)

    def complete_payment(self):
        print("결제 완료!")
        self.switch_callback('home')

if __name__ == '__main__':
    import sys
    from model.cart_data import CartData
    app = QApplication(sys.argv)

    def dummy_callback(screen):
        print(f"Callback called: {screen}")

    dummy_data = CartData()
    window = CheckScreen(dummy_callback, dummy_data)
    window.show()

    sys.exit(app.exec())
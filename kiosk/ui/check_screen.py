from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class CheckScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.init_ui()
        print("CheckScreen initialized")
    
    def init_ui(self):
        print("[DEBUG] CheckScreen")
        layout = QVBoxLayout()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        status_bar = QLabel("주문 내역 확인")
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

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedSize(1018, 1348)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #F5E7C6;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #F5E7C6;
            }
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #F5E7C6;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(7)
        
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
            scroll_layout.addWidget(item)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        content_layout.addWidget(scroll_area, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(content_layout)
        layout.addSpacing(40)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(30)
        
        call_btn = QPushButton("뒤로")
        call_btn.setStyleSheet("""
            QPushButton {
                font-size: 50px;
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
        call_btn.clicked.connect(lambda: self.switch_callback('product'))
        
        pay_btn = QPushButton("결제")
        pay_btn.setStyleSheet("""
            QPushButton {
                font-size: 70px;
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
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)

    def complete_payment(self):
        print("결제 완료!")
        self.switch_callback('home')

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    
    def dummy_callback(screen):
        print(f"Callback called: {screen}")
    
    window = CheckScreen(dummy_callback)
    window.show()
    
    sys.exit(app.exec())
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel)
from PyQt6.QtCore import Qt

class ProductScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.selected_items = []
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
        
        # opencv hear

        # rectangle hear
        
        layout.addSpacing(30)
        
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
        call_btn.clicked.connect(lambda: self.switch_callback('home'))
        
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
        pay_btn.clicked.connect(lambda: self.switch_callback('check'))

        button_layout.addWidget(call_btn)
        button_layout.addWidget(pay_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def add_product(self, product):
        self.selected_items.append(product)
        print(f"선택됨: {product['name']}")

# 테스트 코드
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    
    def dummy_callback():
        print("Callback called")
    
    window = ProductScreen(dummy_callback)
    window.show()
    
    sys.exit(app.exec())
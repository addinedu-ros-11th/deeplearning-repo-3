from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel)

class PaymentScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("결제")
        title.setStyleSheet("font-size: 36px; font-weight: bold;")
        
        amount = QLabel("총액: 9,500원")
        amount.setStyleSheet("font-size: 28px; margin: 30px;")
        
        layout.addWidget(title)
        layout.addWidget(amount)
        layout.addSpacing(40)
        
        # 결제 방법 버튼들
        card_btn = QPushButton("카드 결제")
        card_btn.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                padding: 30px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
            }
        """)
        card_btn.clicked.connect(self.complete_payment)
        
        cash_btn = QPushButton("현금 결제")
        cash_btn.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                padding: 30px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
            }
        """)
        cash_btn.clicked.connect(self.complete_payment)
        
        back_btn = QPushButton("뒤로")
        back_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                padding: 15px;
                background-color: #9E9E9E;
                color: white;
                border: none;
                border-radius: 5px;
            }
        """)
        back_btn.clicked.connect(lambda: self.switch_callback('product'))
        
        layout.addWidget(card_btn)
        layout.addWidget(cash_btn)
        layout.addSpacing(30)
        layout.addWidget(back_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def complete_payment(self):
        print("결제 완료!")
        self.switch_callback('home')
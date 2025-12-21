from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel)

class ProductScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.selected_items = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("상품 선택")
        title.setStyleSheet("font-size: 36px; font-weight: bold;")
        
        # 상품 버튼들
        products = [
            {"name": "커피", "price": 3000},
            {"name": "음료", "price": 2500},
            {"name": "스낵", "price": 4000}
        ]
        
        for product in products:
            btn = QPushButton(f"{product['name']} - {product['price']:,}원")
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 24px;
                    padding: 30px;
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
            """)
            btn.clicked.connect(
                lambda checked, p=product: self.add_product(p)
            )
            layout.addWidget(btn)
        
        layout.addSpacing(30)
        
        # 네비게이션 버튼
        nav_layout = QVBoxLayout()
        
        payment_btn = QPushButton("결제하기")
        payment_btn.setStyleSheet("""
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
        #payment_btn.clicked.connect(lambda: self.switch_callback('check'))
        payment_btn.clicked.connect(lambda a : print("payment_btn.clicked"))
        
        call_btn = QPushButton("관리자 호출")
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
                background-color: #E55A0F;
            }
        """)
        call_btn.clicked.connect(lambda: self.switch_callback('home'))
        #call_btn.clicked.connect(lambda a : print("back_btn.clicked"))
        
        nav_layout.addWidget(payment_btn)
        nav_layout.addWidget(call_btn)
        
        layout.addLayout(nav_layout)
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
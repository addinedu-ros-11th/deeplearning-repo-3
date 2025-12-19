from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel)

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
                font-size: 20px;
                padding: 15px;
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
            }
        """)
        payment_btn.clicked.connect(lambda: self.switch_callback('check'))
        
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
        back_btn.clicked.connect(lambda: self.switch_callback('home'))
        
        nav_layout.addWidget(payment_btn)
        nav_layout.addWidget(back_btn)
        
        layout.addLayout(nav_layout)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def add_product(self, product):
        self.selected_items.append(product)
        print(f"선택됨: {product['name']}")
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea)
from PyQt6.QtCore import Qt

class ScanScreen(QWidget):
    def __init__(self, switch_callback, data):
        super().__init__()
        self.switch_callback = switch_callback
        self.data = data
        self.selected_items = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # status bar 영역
        status_bar = QLabel("스캔")
        status_bar.setStyleSheet("""
            background-color: rgba(255, 109, 31, 0.7);
            color: #222222;
            font-size: 80pt;
            padding: 20px;
        """)
        status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_bar.setFixedHeight(150)
        layout.addWidget(status_bar)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)
        
        # OpenCV 영역
        self.video_label = QLabel()
        self.video_label.setFixedSize(1010, 680)
        self.video_label.setStyleSheet("background-color: black; border: 2px solid #FF6D1F;")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.video_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(content_layout)
        layout.addSpacing(10)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.setSpacing(100)
        button_layout.setContentsMargins(20, 0, 20, 20)
        
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
                font-size: 50px;
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


        container = QWidget()
        container.setFixedHeight(797)
        container.setStyleSheet("""
            QWidget {
                background-color: #F5E7C6;
                border-top-left-radius: 30px;
                border-top-right-radius: 30px;
            }
        """)
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(797)
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
        
        # 스크롤 안의 컨텐츠 위젯
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("""
                        background-color: transparent;
                        border: none;
                        """)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_layout.setSpacing(7)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)  # 가운데 정렬 추가
        
        # 아이템 예시 (테스트용)
        for i in range(10):
            item = QLabel(f"아이템 {i+1}")
            item.setFixedSize(954, 170)
            item.setStyleSheet("""
                background-color: rgba(250, 243, 225, 0.7);
                border-radius: 3px;
                font-size: 40px;
                padding: 7px;
            """)
            item.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.scroll_layout.addWidget(item, alignment=Qt.AlignmentFlag.AlignHCenter)  # 가운데 정렬
        
        self.scroll_layout.addStretch()
        scroll_area.setWidget(self.scroll_content)
        container_layout.addWidget(scroll_area)
        
        # 하단 전체에 배치
        layout.addWidget(container)
        
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
    
    window = ScanScreen(dummy_callback)
    window.show()
    
    sys.exit(app.exec())
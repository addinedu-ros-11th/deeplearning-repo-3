from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class HomeScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()

        image = QLabel()

        layout.addSpacing(100)
        pixmap = QPixmap('./data/logo.png')
        image.setPixmap(pixmap)
        image.setScaledContents(True)
        image.setFixedSize(850, 850)
        layout.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)

        start_btn = QPushButton("주문 시작")
        start_btn.setStyleSheet("""
            QPushButton {
                font-size: 32px;
                padding: 40px;
                background-color: #FF6D1F;
                color: white;
                border: none;
                border-radius: 30px;
            }
            QPushButton:hover {
                background-color: #E55A0F;
            }
        """)
        start_btn.clicked.connect(lambda: self.switch_callback('scan'))
        
        layout.addStretch()
        layout.addSpacing(40)
        layout.addWidget(start_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        
        self.setLayout(layout)

# 테스트 코드
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    
    def dummy_callback():
        print("Callback called")
    
    window = HomeScreen(dummy_callback)
    window.show()
    
    sys.exit(app.exec())
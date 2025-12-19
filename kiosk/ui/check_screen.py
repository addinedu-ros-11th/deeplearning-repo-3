
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class CheckScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()

        image = QLabel()

        layout.addSpacing(400)
        title = QLabel("카드를 태그해 주세요!")
        title.setStyleSheet("font-size: 48px; font-weight: bold; text-align: center;")

        pixmap = QPixmap('./data/payment.png')
        image.setPixmap(pixmap)
        image.setScaledContents(True)
        image.setFixedSize(850, 850)
        layout.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        
        self.setLayout(layout)

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class PaymentScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()

        image = QLabel()

        layout.addSpacing(400)
        title = QLabel("카드를 태그해 주세요!")
        title.setStyleSheet("font-size: 48px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        pixmap = QPixmap('../data/payment.png')
        scaled_pixmap = pixmap.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image.setPixmap(scaled_pixmap)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        
        self.setLayout(layout)


# 테스트 코드
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    
    def dummy_callback():
        print("Callback called")
    
    window = PaymentScreen(dummy_callback)
    window.show()
    
    sys.exit(app.exec())
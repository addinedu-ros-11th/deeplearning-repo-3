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

        layout.addSpacing(400)
        title = QLabel("카드를 태그해 주세요!")
        title.setStyleSheet("font-size: 48px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        image = QLabel()
        pixmap = QPixmap('./data/payment.png')
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
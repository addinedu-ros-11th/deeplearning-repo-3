from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication)
from PyQt6.QtCore import Qt
from popup.payment_popup import BasePopup

class ErrorPopup(BasePopup):
    """결제 시간 초과 팝업"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("에러 발생")
        
        layout = self.create_layout("에러 발생", "시스템 에러가 발생했습니다. 다시 시도해 주세요.\n")
        
        # 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        # '처음으로' 버튼
        home_btn = self.create_button("처음으로", "#E6DABD", is_primary=False)
        home_btn.clicked.connect(lambda: self.done_with_result('home'))
        button_layout.addWidget(home_btn)
        button_layout.setSpacing(50)
        
        # '재시도' 버튼
        retry_btn = self.create_button("재시도", "#FF6D1F", is_primary=True)
        retry_btn.clicked.connect(lambda: self.done_with_result('retry'))
        button_layout.addWidget(retry_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)


from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication)
from PyQt6.QtCore import Qt
from popup.payment_popup import BasePopup

class CallSuccessPopup(BasePopup):
    """관리자 호출 성공 팝업"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("관리자 호출")
        
        layout = self.create_layout("관리자 호출", "관리자 호출을 완료했습니다.\n")
        
        # 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        # '처음으로' 버튼
        home_btn = self.create_button("처음으로", "#FF6D1F", is_primary=False)
        home_btn.clicked.connect(lambda: self.done_with_result('home'))
        button_layout.addWidget(home_btn)
        button_layout.setSpacing(50)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

class CallAutoSuccessPopup(BasePopup):
    """관리자 자동 호출 성공 팝업"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("관리자 호출")
        
        layout = self.create_layout("관리자 호출", "불명확한 아이템이 존재합니다.\n관리자를 호출합니다.\n")
        
        # 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        # '처음으로' 버튼
        home_btn = self.create_button("처음으로", "#FF6D1F", is_primary=False)
        home_btn.clicked.connect(lambda: self.done_with_result('home'))
        button_layout.addWidget(home_btn)
        button_layout.setSpacing(50)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

class CallFailPopup(BasePopup):
    """관리자 호출 실패 팝업"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("관리자 호출")
        
        layout = self.create_layout("관리자 호출", "관리자 호출에 실패했습니다.\n")
        
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
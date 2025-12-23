from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication)
from PyQt6.QtCore import Qt

class BasePopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result = None
        self.setModal(True)
        self.setFixedSize(600, 400)
        
        # 배경색 설정
        self.setStyleSheet("""
            QDialog {
                background-color: #FAF3E1;
            }
        """)
    
    def create_layout(self, title, message):
        """공통 레이아웃 생성"""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # 제목
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #222222;
            font-size: 32px;
            font-weight: bold;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 메시지
        message_label = QLabel(message)
        message_label.setStyleSheet("""
            color: #222222;
            font-size: 24px;
        """)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        layout.addStretch()
        
        return layout
    
    def create_button(self, text, color, is_primary=False):
        """공통 버튼 스타일"""
        btn = QPushButton(text)
        if is_primary:
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 22px;
                    padding: 15px 30px;
                    background-color: {color};
                    color: #FAF3E1;
                    border: none;
                    border-radius: 30px;
                }}
                QPushButton:hover {{
                    background-color: #E55A0F;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 22px;
                    padding: 15px 30px;
                    background-color: {color};
                    color: #222222;
                    border: none;
                    border-radius: 30px;
                }}
                QPushButton:hover {{
                    background-color: rgba(230, 218, 189, 0.7);
                }}
            """)
        return btn
    
    def done_with_result(self, result):
        self.result = result
        self.accept()


class PaymentTimeoutPopup(BasePopup):
    """결제 시간 초과 팝업"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("결제 시간 초과")
        
        layout = self.create_layout("결제 시간 초과", "결제시간이 초과되었습니다.\n다시 시도해주세요.")
        
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


class PaymentCompletePopup(BasePopup):
    """결제 완료 팝업"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("결제 완료")
        
        layout = self.create_layout("결제 완료", "결제가 완료되었습니다!")
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        # '처음으로' 버튼
        home_btn = self.create_button("처음으로", "#FF6D1F", is_primary=True)
        home_btn.clicked.connect(lambda: self.done_with_result('home'))
        button_layout.addWidget(home_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
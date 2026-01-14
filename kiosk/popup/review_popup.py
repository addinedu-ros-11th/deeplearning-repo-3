from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout
from popup.payment_popup import BasePopup


class ReviewPopup(BasePopup):
    """모호한 상품 경고 팝업"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("확인 필요")

        layout = self.create_layout(
            "확인 필요",
            "모호한 상품이 존재합니다.\n직접 확인 후 결제해 주세요."
        )

        # 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        # '확인' 버튼
        confirm_btn = self.create_button("확인", "#FF6D1F", is_primary=True)
        confirm_btn.clicked.connect(lambda: self.done_with_result('confirm'))
        button_layout.addWidget(confirm_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

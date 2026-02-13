"""
키오스크 애플리케이션을 위한 재사용 가능한 PyQt UI 컴포넌트.
공통 스타일링과 위젯 패턴을 중앙화합니다.
"""
from PyQt6.QtWidgets import (
    QPushButton, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
)
from PyQt6.QtCore import Qt

from kiosk.constants import UI_STYLE_CONFIG, DETECTION_OVERLAY_CONFIG


class StyledButton(QPushButton):
    """공통 키오스크 스타일링이 적용된 기본 스타일 버튼."""

    PRIMARY_STYLE = f"""
        QPushButton {{
            font-size: {UI_STYLE_CONFIG.FONT_SIZE_MEDIUM}px;
            padding: 15px;
            background-color: {UI_STYLE_CONFIG.PRIMARY_COLOR};
            color: white;
            border: none;
            border-radius: {UI_STYLE_CONFIG.BORDER_RADIUS}px;
        }}
        QPushButton:hover {{
            background-color: #E55A0F;
        }}
        QPushButton:disabled {{
            background-color: {UI_STYLE_CONFIG.DISABLED_COLOR};
            color: {UI_STYLE_CONFIG.DISABLED_TEXT_COLOR};
        }}
    """

    SECONDARY_STYLE = f"""
        QPushButton {{
            font-size: {UI_STYLE_CONFIG.FONT_SIZE_MEDIUM}px;
            padding: 15px;
            background-color: {UI_STYLE_CONFIG.SECONDARY_COLOR};
            color: white;
            border: none;
            border-radius: {UI_STYLE_CONFIG.BORDER_RADIUS}px;
        }}
        QPushButton:hover {{
            background-color: rgba(230, 218, 189, 0.5);
        }}
    """

    def __init__(self, text: str, variant: str = "primary", parent=None):
        super().__init__(text, parent)
        self.set_variant(variant)

    def set_variant(self, variant: str):
        """버튼 스타일 변형을 설정합니다."""
        if variant == "primary":
            self.setStyleSheet(self.PRIMARY_STYLE)
        elif variant == "secondary":
            self.setStyleSheet(self.SECONDARY_STYLE)


class StatusBar(QLabel):
    """화면 헤더용 스타일 상태 바."""

    STYLE = f"""
        background-color: rgba(255, 109, 31, 0.7);
        color: #222222;
        font-size: {UI_STYLE_CONFIG.FONT_SIZE_LARGE}pt;
        padding: 20px;
    """

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(self.STYLE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(150)


class ItemCard(QWidget):
    """아이템 정보를 표시하는 카드 위젯."""

    CONTAINER_STYLE = """
        background-color: rgba(250, 243, 225, 0.7);
        border-radius: 10px;
    """

    LABEL_STYLE = f"font-size: {UI_STYLE_CONFIG.FONT_SIZE_SMALL}px; background: transparent;"

    def __init__(self, name: str, price: int, qty: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(954, 100)
        self.setStyleSheet(self.CONTAINER_STYLE)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 15, 30, 15)

        # 이름 라벨 (왼쪽)
        name_label = QLabel(name)
        name_label.setStyleSheet(self.LABEL_STYLE)
        name_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        # 가격 라벨 (오른쪽)
        price_label = QLabel(f"{price:,}원 x {qty}")
        price_label.setStyleSheet(self.LABEL_STYLE)
        price_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addWidget(name_label)
        layout.addWidget(price_label)


class ContentContainer(QWidget):
    """메인 콘텐츠 영역을 위한 스타일 컨테이너."""

    STYLE = f"""
        QWidget {{
            background-color: {UI_STYLE_CONFIG.BACKGROUND_COLOR};
            border-top-left-radius: {UI_STYLE_CONFIG.BORDER_RADIUS}px;
            border-top-right-radius: {UI_STYLE_CONFIG.BORDER_RADIUS}px;
        }}
    """

    def __init__(self, height: int = 797, parent=None):
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setStyleSheet(self.STYLE)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)


class StyledScrollArea(QScrollArea):
    """일관된 외관을 가진 스타일 스크롤 영역."""

    STYLE = f"""
        QScrollArea {{
            background-color: {UI_STYLE_CONFIG.BACKGROUND_COLOR};
            border: none;
            border-top-left-radius: {UI_STYLE_CONFIG.BORDER_RADIUS}px;
            border-top-right-radius: {UI_STYLE_CONFIG.BORDER_RADIUS}px;
            padding-top: 10px;
            padding-right: 10px;
        }}
        QScrollBar:vertical {{
            background-color: {UI_STYLE_CONFIG.BACKGROUND_COLOR};
            width: 10px;
            margin: 30px 5px 0px 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: rgba(255, 109, 31, 0.5);
            border-radius: 5px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """

    def __init__(self, height: int = 797, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFixedHeight(height)
        self.setStyleSheet(self.STYLE)


class EmptyStateLabel(QLabel):
    """빈 상태 메시지를 위한 라벨."""

    STYLE = """
        font-size: 45px;
        color: rgba(0, 0, 0, 0.3);
        padding: 50px;
    """

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(self.STYLE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class VideoDisplay(QLabel):
    """스타일이 적용된 비디오 표시 영역."""

    STYLE = f"background-color: black; border: 2px solid {UI_STYLE_CONFIG.PRIMARY_COLOR};"

    def __init__(self, width: int = 1010, height: int = 680, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setStyleSheet(self.STYLE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


def get_detection_color(state: str) -> tuple:
    """감지 상태에 대한 색상을 반환합니다."""
    colors = {
        "AUTO": DETECTION_OVERLAY_CONFIG.COLOR_AUTO,
        "REVIEW": DETECTION_OVERLAY_CONFIG.COLOR_REVIEW,
        "UNKNOWN": DETECTION_OVERLAY_CONFIG.COLOR_UNKNOWN,
    }
    return colors.get(state, DETECTION_OVERLAY_CONFIG.COLOR_UNKNOWN)


def create_button_layout(buttons: list, spacing: int = 100) -> QHBoxLayout:
    """버튼들을 포함한 가로 레이아웃을 생성합니다."""
    layout = QHBoxLayout()
    layout.setSpacing(spacing)
    layout.setContentsMargins(20, 0, 20, 20)

    for button in buttons:
        layout.addWidget(button)

    return layout

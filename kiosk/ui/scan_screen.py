from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea)
from PyQt6.QtCore import Qt
from thread.server_worker import APIWorker
from popup.error_popup import ErrorPopup
import logging
import uuid

class ScanScreen(QWidget):
    def __init__(self, switch_callback, data, store_id, device_id):
        super().__init__()
        self.switch_callback = switch_callback
        self.data = data
        self.selected_items = []
        self.session_id = None
        self.store_id = store_id
        self.checkout_device_id = device_id
        self.init_ui()

        self.create_session()
        
    def create_session(self):
        """서버에 새 세션 생성 요청 (비동기)"""
        session_uuid = str(uuid.uuid4())
        
        session_data = {
            "store_id": self.store_id,
            "checkout_device_id": self.checkout_device_id,
            "session_uuid": session_uuid,
            "attempt_limit": 3
        }
        
        logging.info("[세션생성] 세션 생성 요청 시작")
        
        # APIWorker로 비동기 요청
        self.session_worker = APIWorker(
            api_url="/api/v1/sessions/create",
            method="POST",
            data=session_data
        )
        
        # 시그널 연결
        self.session_worker.success.connect(self.on_session_created)
        self.session_worker.error.connect(self.on_session_error)
        self.session_worker.finished.connect(self.on_session_finished)
        
        # 스레드 시작
        self.session_worker.start()
    
    def on_session_created(self, result):
        """세션 생성 성공"""
        self.session_id = result.get("session_id")
        self.data.set_session_id(self.session_id)
        self.data.set_store_id(self.store_id)

        logging.info(f"[세션생성] 세션 생성 완료: {self.session_id}")
    
    def on_session_error(self, error_msg):
        """세션 생성 실패"""
        logging.error(f"[세션생성] 세션 생성 실패: {error_msg}")

        # 사용자에게 에러 표시
        error_popup = ErrorPopup()
        error_popup.exec()

        if error_popup.result == 'home':
            self.switch_callback('home')
        elif error_popup.result == 'retry':
            # 세션 재생성 시도
            logging.info("[세션생성] 세션 재생성 시도")
            self.create_session()
    
    def on_session_finished(self):
        """세션 생성 요청 완료 (성공/실패 무관)"""
        logging.info("[세션생성] 세션 생성 요청 종료")
        self.session_worker = None

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
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        # 초기 안내 메시지 (아이템이 없을 때)
        self.empty_label = QLabel("트레이를 올려주세요")
        self.empty_label.setStyleSheet("""
            font-size: 45px;
            color: rgba(0, 0, 0, 0.3);
            padding: 50px;
        """)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_layout.addWidget(self.empty_label)
        
        self.scroll_layout.addStretch()
        scroll_area.setWidget(self.scroll_content)
        container_layout.addWidget(scroll_area)
        
        # 하단 전체에 배치
        layout.addWidget(container)
        
        self.setLayout(layout)
    
    def add_product(self, product):
        self.selected_items.append(product)
        print(f"선택됨: {product['name']}")
    
    def add_scanned_item(self, item_name: str):
        """스캔된 아이템 이름으로 서버에서 정보 조회 후 장바구니에 추가"""
        # 이미 있는 아이템인지 확인 (이름 기준)
        existing_item = None
        for item in self.data.items:
            if item["name"] == item_name:
                existing_item = item
                break

        if existing_item:
            # 수량 증가
            existing_item["qty"] += 1
            self.update_item_list()
            logging.info(f"아이템 수량 증가: {item_name}")
        else:
            # 서버에서 item_id, price_won 조회
            self.fetch_menu_item(item_name)

    def fetch_menu_item(self, item_name: str):
        """서버에서 메뉴 아이템 정보 조회"""
        self.menu_worker = APIWorker(
            api_url=f"/api/v1/menu-items/{item_name}",
            method="GET"
        )
        self.menu_worker.success.connect(lambda result: self.on_menu_item_fetched(result))
        self.menu_worker.error.connect(lambda err: self.on_menu_item_error(err, item_name))
        self.menu_worker.start()

    def on_menu_item_fetched(self, result):
        """메뉴 아이템 정보 조회 성공"""
        self.data.items.append({
            "item_id": result["item_id"],
            "name": result["name_kor"],
            "qty": 1,
            "unit_price": result["price_won"]
        })
        self.update_item_list()
        logging.info(f"아이템 추가: {result['name_kor']} (id: {result['item_id']}, price: {result['price_won']})")

    def on_menu_item_error(self, error_msg, item_name):
        """메뉴 아이템 정보 조회 실패"""
        logging.error(f"[메뉴조회] {item_name} 조회 실패: {error_msg}")
    
    def update_item_list(self):
        """스크롤 영역의 아이템 목록 업데이트"""
        # 기존 위젯 모두 제거
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                self.scroll_layout.removeItem(item)
        
        # 아이템이 없으면 안내 메시지 표시
        if not self.data.items:
            empty_label = QLabel("트레이를 올려주세요")
            empty_label.setStyleSheet("""
                font-size: 45px;
                color: rgba(0, 0, 0, 0.3);
                padding: 50px;
            """)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty_label)
        else:
            # 아이템 목록 표시
            for item in self.data.items:
                item_widget = QLabel(
                    f"{item['name']} x{item['qty']} - {item['unit_price'] * item['qty']:,}원"
                )
                item_widget.setFixedSize(954, 170)
                item_widget.setStyleSheet("""
                    background-color: rgba(250, 243, 225, 0.7);
                    border-radius: 3px;
                    font-size: 40px;
                    padding: 7px;
                """)
                item_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.scroll_layout.addWidget(item_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        self.scroll_layout.addStretch()


# 테스트 코드
if __name__ == '__main__':
    import sys
    from model.cart_data import CartData
    app = QApplication(sys.argv)

    def dummy_callback(screen):
        print(f"Callback called: {screen}")

    dummy_data = CartData()
    window = ScanScreen(dummy_callback, dummy_data, store_id=1, device_id=1)
    window.show()

    sys.exit(app.exec())
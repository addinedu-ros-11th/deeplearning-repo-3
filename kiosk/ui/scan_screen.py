from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from thread.server_worker import APIWorker
from thread.infer_worker import InferWorker
from popup.error_popup import ErrorPopup
import logging
import uuid
import cv2

class ScanScreen(QWidget):
    def __init__(self, switch_callback, data, store_id, device_id):
        super().__init__()
        self.switch_callback = switch_callback
        self.data = data
        self.selected_items = []
        self.session_id = None
        self.session_uuid = None
        self.store_id = store_id
        self.checkout_device_id = device_id
        self.is_inferring = False  # AI 추론 중 여부

        # 웹캠 초기화
        self.cap = None
        self.camera_timer = None
        self.current_frame = None  # 현재 프레임 저장

        # 트레이 감지용 변수 (ROI 밝기 기반)
        self.tray_detected = False  # 트레이 감지 상태
        self.stable_count = 0  # 안정화 카운트
        self.STABLE_THRESHOLD = 10  # 안정화 판단 프레임 수 (~0.3초)
        self.BRIGHTNESS_THRESHOLD = 100  # 트레이 감지 밝기 임계값 (0-255)
        self.ROI_RATIO = (0.3, 0.3, 0.7, 0.7)  # ROI 영역 비율 (x1, y1, x2, y2)

        # 메뉴 조회 대기 목록
        self.pending_items = []

        self.init_ui()
        self.create_session()
        
    def create_session(self):
        """서버에 새 세션 생성 요청 (비동기)"""
        self.session_uuid = str(uuid.uuid4())

        session_data = {
            "store_id": self.store_id,
            "checkout_device_id": self.checkout_device_id,
            "session_uuid": self.session_uuid,
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
        self.data.set_session_uuid(self.session_uuid)
        self.data.set_store_id(self.store_id)

        logging.info(f"[세션생성] 세션 생성 완료: {self.session_id}, UUID: {self.session_uuid}")

        # 세션 생성 완료 후 웹캠 시작
        self.start_camera()
    
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

        self.pay_btn = QPushButton("결제")
        self.pay_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.pay_btn.clicked.connect(lambda: self.switch_callback('check'))

        button_layout.addWidget(call_btn)
        button_layout.addWidget(self.pay_btn)

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
                item_container = QWidget()
                item_container.setFixedSize(954, 100)
                item_container.setStyleSheet("""
                    background-color: rgba(250, 243, 225, 0.7);
                    border-radius: 10px;
                """)

                item_layout = QHBoxLayout(item_container)
                item_layout.setContentsMargins(30, 15, 30, 15)

                # 이름 (왼쪽)
                name_label = QLabel(item['name'])
                name_label.setStyleSheet("font-size: 36px; background: transparent;")
                name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                # 단가 x 개수 (오른쪽)
                price_label = QLabel(f"{item['unit_price']:,}원 x {item['qty']}")
                price_label.setStyleSheet("font-size: 36px; background: transparent;")
                price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                item_layout.addWidget(name_label)
                item_layout.addWidget(price_label)

                self.scroll_layout.addWidget(item_container, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        self.scroll_layout.addStretch()

    # ========================================
    # 웹캠 관련 메서드
    # ========================================
    def start_camera(self):
        """웹캠 시작"""
        if self.cap is not None:
            return  # 이미 실행 중

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            logging.error("[웹캠] 카메라를 열 수 없습니다")
            return

        logging.info("[웹캠] 카메라 시작")

        # 30fps로 프레임 업데이트
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_frame)
        self.camera_timer.start(33)  # ~30fps

    def stop_camera(self):
        """웹캠 중지"""
        if self.camera_timer:
            self.camera_timer.stop()
            self.camera_timer = None

        if self.cap:
            self.cap.release()
            self.cap = None
            logging.info("[웹캠] 카메라 중지")

    def update_frame(self):
        """웹캠 프레임 업데이트"""
        if self.cap is None or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        # 현재 프레임 저장 (AI 추론용)
        self.current_frame = frame.copy()

        # 트레이 감지 로직
        self.detect_tray(frame)

        # BGR -> RGB 변환
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # QImage로 변환
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # QLabel 크기에 맞게 스케일링
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)

    def detect_tray(self, frame):
        """ROI 영역의 밝기 변화로 트레이 감지 (검은색 -> 흰색)"""
        if self.is_inferring:
            return  # 추론 중이면 감지 안함

        h, w = frame.shape[:2]
        x1 = int(w * self.ROI_RATIO[0])
        y1 = int(h * self.ROI_RATIO[1])
        x2 = int(w * self.ROI_RATIO[2])
        y2 = int(h * self.ROI_RATIO[3])

        # ROI 영역 추출
        roi = frame[y1:y2, x1:x2]

        # 그레이스케일 변환 후 평균 밝기 계산
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        avg_brightness = gray_roi.mean()

        # 트레이 감지 (밝기가 임계값 이상이면 트레이 있음)
        is_bright = avg_brightness >= self.BRIGHTNESS_THRESHOLD

        if is_bright:
            if not self.tray_detected:
                # 트레이가 새로 감지됨
                self.tray_detected = True
                self.stable_count = 0
                logging.info(f"[트레이감지] 트레이 감지됨 (밝기: {avg_brightness:.1f})")
            else:
                # 트레이가 계속 있음 - 안정화 카운트 증가
                self.stable_count += 1
                if self.stable_count == self.STABLE_THRESHOLD:
                    logging.info("[트레이감지] 트레이 안정화 - AI 추론 시작")
                    self.start_inference()
        else:
            # 트레이 없음 (어두움)
            if self.tray_detected:
                logging.info(f"[트레이감지] 트레이 제거됨 (밝기: {avg_brightness:.1f})")
            self.tray_detected = False
            self.stable_count = 0

    def hideEvent(self, event):
        """화면이 숨겨질 때 웹캠 중지"""
        super().hideEvent(event)
        self.stop_camera()

    # ========================================
    # AI 추론 관련 메서드
    # ========================================
    def start_inference(self):
        """현재 프레임으로 AI 추론 시작"""
        if self.is_inferring:
            logging.warning("[AI추론] 이미 추론 중입니다")
            return

        if self.current_frame is None:
            logging.warning("[AI추론] 캡처된 프레임이 없습니다")
            return

        if not self.session_uuid:
            logging.error("[AI추론] 세션 UUID가 없습니다")
            return

        self.is_inferring = True
        logging.info("[AI추론] AI 추론 시작")

        # 테스트: 웹캠 대신 테스트 이미지 사용
        import os
        test_image_path = os.path.join(os.path.dirname(__file__), "..", "data", "tray_test.png")
        if os.path.exists(test_image_path):
            with open(test_image_path, "rb") as f:
                frame_bytes = f.read()
            logging.info(f"[AI추론] 테스트 이미지 사용: {test_image_path}")
        else:
            # 프레임을 JPEG로 인코딩
            _, buffer = cv2.imencode('.jpg', self.current_frame)
            frame_bytes = buffer.tobytes()

        # AI 추론 Worker 실행
        self.infer_worker = InferWorker(
            session_uuid=self.session_uuid,
            frame_bytes=frame_bytes,
            store_code=f"STORE-{self.store_id:02d}",
            device_code=f"POS-{self.checkout_device_id:02d}"
        )
        self.infer_worker.success.connect(self.on_inference_success)
        self.infer_worker.error.connect(self.on_inference_error)
        self.infer_worker.start()

    def on_inference_success(self, result):
        """AI 추론 성공"""
        self.is_inferring = False
        decision = result.get("decision", "UNKNOWN")
        result_json = result.get("result_json", {})

        logging.info(f"[AI추론] 결과: decision={decision}, result_json={result_json}")

        # 실제 환경에선 아래 주석 해제 필요
        if decision == "AUTO":
            # 인식된 아이템을 장바구니에 추가 + 결제 버튼 활성화
            self.process_inference_result(result_json)
            self.pay_btn.setEnabled(True)
            
        elif decision == "REVIEW":
            # 아이템 표시하되 결제 버튼 비활성화
            logging.warning("[AI추론] 수동 검토 필요 - 결제 버튼 비활성화")
            self.process_inference_result(result_json)
            self.pay_btn.setEnabled(False)
            
        else:
            logging.warning(f"[AI추론] 알 수 없는 결과: {decision}")
            self.pay_btn.setEnabled(False)

    def on_inference_error(self, error_msg):
        """AI 추론 실패"""
        self.is_inferring = False
        logging.error(f"[AI추론] 오류: {error_msg}")

    def process_inference_result(self, result_json):
        """AI 추론 결과를 장바구니에 반영"""
        # result_json.items 또는 result_json.instances에서 아이템 추출
        items = result_json.get("items") or result_json.get("instances") or []

        # 조회할 item_id 목록 수집
        self.pending_items = []
        for item in items:
            item_id = item.get("item_id") or item.get("best_item_id") or item.get("menu_item_id")
            qty = item.get("qty") or item.get("count") or 1

            if item_id is None:
                continue

            self.pending_items.append({"item_id": item_id, "qty": qty})

        # 순차적으로 메뉴 정보 조회
        self.fetch_next_menu_item()

    def fetch_next_menu_item(self):
        """대기 중인 아이템의 메뉴 정보 조회"""
        if not self.pending_items:
            # 모든 아이템 조회 완료 - UI 업데이트
            self.update_item_list()
            logging.info(f"[AI추론] 장바구니 업데이트 완료: {len(self.data.items)}개 아이템")
            return

        item = self.pending_items.pop(0)
        item_id = item["item_id"]
        qty = item["qty"]

        # 서버에서 메뉴 정보 조회
        self.menu_worker = APIWorker(
            api_url=f"/api/v1/menu-items/by-id/{item_id}",
            method="GET"
        )
        self.menu_worker.success.connect(lambda result: self.on_menu_fetched(result, qty))
        self.menu_worker.error.connect(lambda err: self.on_menu_fetch_error(err, item_id, qty))
        self.menu_worker.start()

    def on_menu_fetched(self, result, qty):
        """메뉴 정보 조회 성공"""
        item_id = result.get("item_id")
        name = result.get("name_kor") or result.get("name_eng") or f"상품 #{item_id}"
        unit_price = result.get("price_won") or 0

        # 이미 장바구니에 있는지 확인
        existing = next((i for i in self.data.items if i["item_id"] == item_id), None)
        if existing:
            existing["qty"] += qty
        else:
            self.data.items.append({
                "item_id": item_id,
                "name": name,
                "qty": qty,
                "unit_price": unit_price
            })

        logging.info(f"[메뉴조회] {name} (id:{item_id}, {unit_price}원) 추가됨")

        # 다음 아이템 조회
        self.fetch_next_menu_item()

    def on_menu_fetch_error(self, error_msg, item_id, qty):
        """메뉴 정보 조회 실패 - 기본값으로 추가"""
        logging.error(f"[메뉴조회] item_id={item_id} 조회 실패: {error_msg}")

        # 기본값으로 장바구니에 추가
        existing = next((i for i in self.data.items if i["item_id"] == item_id), None)
        if existing:
            existing["qty"] += qty
        else:
            self.data.items.append({
                "item_id": item_id,
                "name": f"상품 #{item_id}",
                "qty": qty,
                "unit_price": 0
            })

        # 다음 아이템 조회
        self.fetch_next_menu_item()


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
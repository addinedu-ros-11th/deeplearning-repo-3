import serial
import threading

class RFIDPayment:
    def __init__(self, port="/dev/ttyACM0", baudrate=9600):
        self.pay_status = ""   # 결제 완료 여부
        self.last_uid = None # 마지막 인식된 카드 확인
        
        self.ser = serial.Serial(port, baudrate, timeout=1)
        
        # 카드별 결제
        self.card_result = {
            "61097506": "PAY_OK",     # 61097506 카드 : 결제 가능(카드)
            "05FB4E06": "NO_MONEY"    # 05FB4E06 카드 : 잔액 부족(태그)
        }

        # 시리얼 수신 스레드 시작
        self._thread =  threading.Thread(
            target = self._listen_serial,
            daemon = True 
        )
        self._thread.start()

    def _listen_serial(self):
        """Arduino에서 UID 수신"""
        while True:
            if self.ser.in_waiting:
                line = self.ser.readline().decode("utf-8").strip()
                print("[RFID]", line)

                if line.startswith("UID:"):
                    uid = line.split(":")[1]
                    self.last_uid = uid
                    self._process_payment(uid)
                    
    def _process_payment(self, uid):
        """UID 기준 결제 결과 판단"""
        if uid in self.card_result:
            self.pay_status = self.card_result[uid]
        else:
            self.pay_status = "NO_CARD"   # 등록 안 된 카드
            
    def get_status(self):
        """현재 결제 상태 반환 
        ("PAY_OK", "NO_MONEY", "NO_CARD")
        """
        return self.pay_status
    
    def get_uid(self):
        """마지막 인식된 카드 UID"""
        return self.last_uid

    def reset(self):
        """다음 손님 대비 초기화"""
        self.pay_status = ""
        self.last_uid = None
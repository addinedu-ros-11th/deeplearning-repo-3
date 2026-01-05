import serial
import threading
import time

class RFIDPayment:
    def __init__(self, port="/dev/ttyACM0", baudrate=9600):
        self.is_payed = False   # 결제 완료 여부
        self.ser = serial.Serial(port, baudrate, timeout=1)

        # 시리얼 수신 스레드 시작
        self._thread =  threading.Thread(
            target = self._listen_serial,
            daemon = True 
        )
        self._thread.start()

    def _listen_serial(self):
        """Arduino에서 오는 PAY_Ok 신호"""
        while True:
            if self.ser.in_waiting:
                line = self.ser.readline().decode("utf-8").strip()
                print("[RFID]", line)

                if line == "PAY_OK":
                    self.is_payed = True

    def check_pay(self):
        """UI에서 주기적으로 호출"""
        return self.is_payed

    def reset(self):
        """결제 상태 초기화 (다음 결제 대비)"""
        self.is_payed = False
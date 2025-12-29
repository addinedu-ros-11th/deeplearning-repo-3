class RFIDPayment():
    def __init__(self):
        self.is_payed = False # 결제가 완료되면 해당 변수를 True로 변경.

    def check_pay(self):
        """UI랑 연결되는 함수"""
        return self.is_payed
class CartData:
    def __init__(self):
        self.store_id = None
        self.session_id = None
        self.session_uuid = None
        self.items = []  # {"item_id": 1, "name": "커피", "qty": 2, "unit_price": 5000}

    def set_store_id(self, store_id):
        self.store_id = store_id

    def set_session_id(self, session_id):
        self.session_id = session_id

    def set_session_uuid(self, session_uuid):
        self.session_uuid = session_uuid

    def get_store_id(self):
        return self.store_id

    def get_session_id(self):
        return self.session_id

    def get_session_uuid(self):
        return self.session_uuid
    
    def get_item_ids(self):
        return [item["item_id"] for item in self.items]
    
    def get_item_name(self):
        return [item["name"] for item in self.items]
    
    def get_item_quantity(self):
        return [item["qty"] for item in self.items]
    
    def get_unit_prices(self):
        return [item["unit_price"] for item in self.items]
    
    def get_total_amount(self):
        return sum(item["qty"] * item["unit_price"] for item in self.items)
    
    def clear(self):
        """주문 완료 후 장바구니 초기화"""
        self.items = []
        self.session_id = None
        self.session_uuid = None
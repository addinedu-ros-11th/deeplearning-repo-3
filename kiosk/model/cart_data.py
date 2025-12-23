class CartData:
    def __init__(self):
        self.items = []  # 장바구니 아이템
        self.total_quantity = 0
        self.total_amount = 0
    
    def add_item(self, item):
        """아이템 추가"""
        self.items.append(item)
        self._update_totals()
    
    def remove_item(self, item):
        """아이템 제거"""
        if item in self.items:
            self.items.remove(item)
            self._update_totals()
    
    def clear_items(self):
        """모든 아이템 삭제"""
        self.items.clear()
        self._update_totals()
    
    def _update_totals(self):
        """총 수량, 총액 업데이트"""
        self.total_quantity = len(self.items)
        self.total_amount = sum(item.get('price', 0) for item in self.items)

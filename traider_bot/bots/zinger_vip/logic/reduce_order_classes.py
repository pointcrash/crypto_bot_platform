from decimal import Decimal


class LongReduceOrder:
    def __init__(self, qty, price, percent):
        self.psn_side = 'LONG'
        self.psn_qty = Decimal(qty)
        self.psn_price = Decimal(price)
        self.psn_cost = self.psn_price * self.psn_qty

        self.order_price = self.psn_price + (self.psn_price * percent)
        self.order_cost = self.order_price * self.psn_qty
        self.cost_diff = abs(self.order_cost - self.psn_cost)
        self.coin_sold_count = self.cost_diff / self.order_price
        self.qty_after_sold = self.psn_qty - self.coin_sold_count


class ShortReduceOrder:
    def __init__(self, qty, price, percent):
        self.psn_side = 'SHORT'
        self.psn_qty = Decimal(qty)
        self.psn_price = Decimal(price)

        self.order_price = self.psn_price - (self.psn_price * percent)
        self.order_cost = self.order_price * self.psn_qty
        self.cost_after_reduction = self.order_cost - (self.order_cost * percent)
        self.qty_after_sold = self.cost_after_reduction / self.order_price
        self.coin_sold_count = self.psn_qty - self.qty_after_sold


class LongShortDataClass:
    def __into__(self):
        self.long = []
        self.short = []

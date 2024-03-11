from decimal import Decimal


class LongReduceOrder:
    def __into__(self, psn, percent):
        self.psn_side = psn['side']
        self.psn_qty = Decimal(psn['qty'])
        self.psn_price = Decimal(psn['entryPrice'])
        self.psn_cost = self.psn_price * self.psn_qty

        self.order_price = self.psn_price + (self.psn_price * percent)
        self.order_cost = self.order_price * self.psn_qty
        self.cost_diff = abs(self.order_cost - self.psn_cost)
        self.coin_sold_count = self.cost_diff / self.order_price
        self.qty_after_sold = self.psn_qty - self.coin_sold_count


class ShortReduceOrder:
    def __into__(self, psn, percent):
        self.psn_side = psn['side']
        self.psn_qty = Decimal(psn['qty'])
        self.psn_price = Decimal(psn['entryPrice'])
        self.psn_cost = self.psn_price * self.psn_qty

        self.order_price = self.psn_price - (self.psn_price * percent)
        self.order_cost = self.order_price * self.psn_qty
        self.cost_after_reduction = self.order_cost - (self.order_cost * percent)
        self.qty_after_sold = self.cost_after_reduction / self.order_price
        self.coin_sold_count = self.psn_qty - self.qty_after_sold


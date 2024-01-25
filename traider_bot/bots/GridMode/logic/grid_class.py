from api.api_v5_bybit import get_list, cancel_all, switch_position_mode, set_leverage, get_current_price
from bots.bot_logic import get_quantity_from_price, logging
from orders.models import Order


class GridClassLogic:

    def __init__(self, bot):
        self.bot = bot
        self.bot_id = bot.pk
        self.account = bot.account
        self.category = bot.category
        self.side = bot.side
        self.qty = bot.qty
        self.symbol = bot.symbol
        self.leverage = bot.isLeverage
        self.price = bot.price
        self.round_number = int(bot.symbol.priceScale)
        self.symbol_list = get_list(bot.account, symbol=bot.symbol)

    def preparatory_actions(self):
        cancel_all(self.account, self.category, self.symbol)
        switch_position_mode(self.bot)
        set_leverage(self.account, self.category, self.symbol, self.leverage, self.bot)

    def open_psn(self):
        order_type = "Limit" if self.price else "Market"

        Order.objects.create(
            bot=self.bot,
            category=self.category,
            symbol=self.symbol.name,
            side=self.side,
            orderType=order_type,
            qty=get_quantity_from_price(
                self.qty,
                self.price if self.price else get_current_price(self.account, self.category, self.symbol),
                self.symbol.minOrderQty,
                self.leverage
            ),
            price=self.price
        )

    def position_status_tracking(self):
        self.symbol_list = get_list(self.account, symbol=self.symbol)

        if float(self.symbol_list[0]['size']) != 0 and float(self.symbol_list[1]['size']) != 0:
            raise Exception('Открыты две позиции')
        elif float(self.symbol_list[0]['size']) != 0:
            psn_size = float(self.symbol_list[0]['size'])
        elif float(self.symbol_list[1]['size']) != 0:
            psn_size = float(self.symbol_list[1]['size'])
        else:
            raise Exception('Позиция отсутствует')


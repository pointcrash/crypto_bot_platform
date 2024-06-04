import logging
import threading
import time
from decimal import Decimal

from django.core.cache import cache

from api_2.api_aggregator import change_position_mode, set_leverage, cancel_all_orders, place_order, \
    get_position_inform, place_conditional_order
from api_2.custom_logging_api import custom_logging
from bots.bb.logic.avg_logic import BBAutoAverage
from bots.bb.logic.bb_class import BollingerBands


class WorkBollingerBandsClass:
    def __init__(self, bot):
        self.bot = bot
        self.symbol = bot.symbol.name
        self.bb = BollingerBands(bot)
        self.avg_obj = BBAutoAverage(bot, self.bb)
        self.ml_filled = bot.bb.take_on_ml_status
        self.ml_qty = bot.bb.take_on_ml_qty
        self.current_price = None
        self.current_order_id = []
        self.have_psn = False
        self.ml_order_id = None
        self.main_order_id = None
        self.sl_order = None
        self.position_info = dict()
        self.count_cycles = 0

        self.psn_locker = threading.Lock()
        self.avg_locker = threading.Lock()
        self.order_locker = threading.Lock()
        self.logger = self.get_logger_for_bot_ws_msg(bot.id)

    def cached_data(self, key, value):
        cache.set(f'bot{self.bot.id}_{key}', str(value))

    def get_logger_for_bot_ws_msg(self, bot_id):
        formatter = logging.Formatter('%(message)s')

        logger = logging.getLogger(f'BOT_{bot_id}_METRICS')
        logger.setLevel(logging.DEBUG)

        handler = logging.FileHandler(f'logs/bots/ws_data/bot_{bot_id}_metrics.log')
        handler.setFormatter(formatter)
        logger.handlers.clear()
        logger.addHandler(handler)

        return logger

    def preparatory_actions(self):
        try:
            change_position_mode(self.bot)
        except:
            pass
        try:
            set_leverage(self.bot)
        except:
            pass

        not_null_psn_list = list(psn for psn in get_position_inform(self.bot) if float(psn['qty']) != 0)

        if len(not_null_psn_list) > 1:
            raise Exception('More than one position')
        elif len(not_null_psn_list) == 1:
            self.count_cycles += 1
            self.have_psn = True
            self.position_info = not_null_psn_list[0]
            self.position_info['qty'] = abs(Decimal(self.position_info['qty']))
            self.avg_obj.update_psn_info(self.position_info)
            # self.replace_closing_orders()
        # else:
        #     self.replace_opening_orders()

    def price_check(self, price, take_number):
        psn_side = self.position_info['side']
        psn_price = Decimal(self.position_info['entryPrice'])
        tick_size = Decimal(self.bot.symbol.tickSize)
        take_distance = tick_size * 6 if take_number == 1 else tick_size * 12

        if psn_side == 'LONG':
            if price < psn_price:
                return psn_price + take_distance
            return price
        elif psn_side == 'SHORT':
            if price > psn_price:
                return psn_price - take_distance
            return price

    def place_open_psn_order(self, current_price):
        if self.bot.bb.endless_cycle or not self.bot.bb.endless_cycle and self.count_cycles == 0:
            self.count_cycles += 1
            side = self.bot.bb.side
            amount_usdt = self.bot.amount_long

            if side == 'FB' or side == 'Buy':
                if current_price <= self.bb.bl:
                    response = place_order(self.bot, side='BUY', order_type='MARKET', price=current_price,
                                           amount_usdt=amount_usdt)
                    if response.get('orderId'):
                        self.current_order_id.append(response['orderId'])
                        self.have_psn = True
                    else:
                        custom_logging(self.bot, response, named='response')
                        raise Exception('Open order is failed')
            if side == 'FB' or side == 'Sell':
                if current_price >= self.bb.tl:
                    response = place_order(self.bot, side='SELL', order_type='MARKET', price=current_price,
                                           amount_usdt=amount_usdt)
                    if response.get('orderId'):
                        self.current_order_id.append(response['orderId'])
                        self.have_psn = True
                    else:
                        custom_logging(self.bot, response, named='response')
                        raise Exception('Open order is failed')

    def place_closing_orders(self):
        position_side = self.position_info['side']
        psn_qty = self.position_info['qty']
        main_take_qty = Decimal(self.position_info['qty'])

        side, price, td = ('SELL', self.bb.tl, 1) if position_side == 'LONG' else ('BUY', self.bb.bl, 2)
        price = self.price_check(price, 2)

        if self.bot.bb.take_on_ml and not self.ml_filled and psn_qty > Decimal(self.bot.symbol.minOrderQty):
            ml_take_price = self.price_check(self.bb.ml, 1)
            if (position_side == 'LONG' and self.current_price > ml_take_price) or (
                    position_side == 'SHORT' and self.current_price < ml_take_price):
                ml_take_qty = Decimal(str(psn_qty * self.bot.bb.take_on_ml_percent / 100)).quantize(
                    Decimal(self.bot.symbol.minOrderQty))

                response = place_order(self.bot, side=side, position_side=position_side, order_type='MARKET',
                                       price=ml_take_price, qty=ml_take_qty)
                self.ml_order_id = response['orderId']
                self.current_order_id.append(response['orderId'])
                self.ml_qty = ml_take_qty
                self.ml_filled = True
                self.ml_status_save()
                main_take_qty = psn_qty - ml_take_qty

        if (position_side == 'LONG' and self.current_price > price) or (
                position_side == 'SHORT' and self.current_price < price):
            response = place_order(self.bot, side=side, position_side=position_side,
                                   price=price, order_type='MARKET', qty=main_take_qty)
            self.main_order_id = response['orderId']
            self.current_order_id.append(response['orderId'])
            self.have_psn = False
            self.ml_qty = 0
            self.ml_filled = False
            self.ml_status_save()
            self.count_cycles += 1

            if self.bot.bb.endless_cycle is False:
                self.bot.is_active = False
                self.bot.save()

    def turn_after_ml(self):
        if self.bot.bb.take_on_ml and self.ml_filled:
            position_side = self.position_info['side']
            order_side = None

            if position_side == 'LONG' and self.current_price < self.bb.bl:
                order_side = 'BUY'
            elif position_side == 'SHORT' and self.current_price > self.bb.tl:
                order_side = 'SELL'

            if order_side:
                response = place_order(self.bot, side=order_side, price=self.current_price, order_type='MARKET',
                                       qty=self.ml_qty)
                self.current_order_id.append(response['orderId'])
                self.ml_qty = 0
                self.ml_filled = False
                self.ml_status_save()

    def place_stop_loss(self):
        if self.bot.bb.sl_order:
            if not self.sl_order:
                pass

    def average(self):
        self.ml_filled = False
        self.ml_qty = 0
        self.ml_status_save()

    def ml_status_save(self):
        bot_bb = self.bot.bb
        bot_bb.take_on_ml_status = self.ml_filled
        bot_bb.take_on_ml_qty = self.ml_qty
        bot_bb.save()

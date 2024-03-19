from binance import ThreadedWebsocketManager
from pybit.unified_trading import WebSocket
from bots.bot_logic import clear_symbols


def connect_to_ws(bot, exchange_service_name):
    ws_connection_list = []
    if exchange_service_name == 'Binance':
        twm = ThreadedWebsocketManager(
            api_key=bot.account.API_TOKEN,
            api_secret=bot.account.SECRET_KEY,
            testnet=not bot.account.is_mainnet
        ).start()
        # twm.start_futures_user_socket(callback=bb_handle_stream_callback(bb_worker_class, 'user_info'))
        # twm.start_symbol_mark_price_socket(callback=bb_handle_stream_callback(bb_worker_class, 'mark_price'),
        #                                    symbol=bot.symbol.name, fast=False)
        # twm.start_kline_socket(callback=bb_handle_stream_callback(bb_worker_class, 'kline'), symbol=bot.symbol.name)
        ws_connection_list.append(twm)

    elif exchange_service_name == 'ByBit':
        ws_private = WebSocket(
            # trace_logging=True,
            testnet=not bot.account.is_mainnet,
            channel_type="private",
            api_key=bot.account.API_TOKEN,
            api_secret=bot.account.SECRET_KEY,
        )
        ws_public = WebSocket(
            testnet=not bot.account.is_mainnet,
            channel_type="linear",
        )
        # ws_private.position_stream(callback=bb_handle_stream_callback(bb_worker_class, arg='position'))
        # ws_private.order_stream(callback=bb_handle_stream_callback(bb_worker_class, arg='order'))
        # ws_public.ticker_stream(symbol=bot.symbol.name,
        #                         callback=bb_handle_stream_callback(bb_worker_class, arg='ticker'))
        ws_connection_list.append(ws_private)
        ws_connection_list.append(ws_public)

    return ws_connection_list


# get_update_symbols_for_binance()
clear_symbols()

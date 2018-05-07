import logging
import time

from backtesting import get_bot
from config.cst import *
from tools.data_visualiser import DataVisualiser


class Backtesting:
    def __init__(self, config, exchange_simulator):
        self.config = config
        self.begin_time = time.time()
        self.time_delta = 0
        self.exchange_simulator = exchange_simulator
        self.logger = logging.getLogger(self.__class__.__name__)

    def end(self):
        self.report()

        # make sure to wait the end of threads process
        time.sleep(3)
        raise Exception("End of simulation in {0} sec".format(time.time() - self.begin_time))

    def report(self):
        market_data = self.exchange_simulator.get_data()[self.exchange_simulator.MIN_ENABLED_TIME_FRAME.value]
        market_data_df = self.exchange_simulator.candles_array_to_data_frame(market_data)

        self.time_delta = self.begin_time - market_data[0][PriceIndexes.IND_PRICE_TIME.value]

        # profitability
        total_profitability = 0
        for trader in get_bot().get_exchange_trader_simulators().values():
            _, profitability, _ = trader.get_trades_manager().get_profitability()
            total_profitability += profitability

        # vs market
        market_delta = self.get_market_delta(market_data)

        # graph
        trade_created = []
        trade_filled = []
        trade_canceled = []
        for trader in get_bot().get_exchange_trader_simulators().values():
            for trade in trader.get_trades_manager().get_trade_history():
                if trade.get_final_status() == OrderStatus.FILLED:
                    trade_filled.append([trade.get_filled_time() - self.time_delta, trade.get_price()])

        indicators_map = [
            {
                "title": "Filled",
                "data": trade_filled,
                "in_graph": True,
                "points": True,
                "share_x": False,
                "share_y": True
            }
        ]
        DataVisualiser.show_candlesticks_dataframe_with_indicators(market_data_df, indicators_map)

        # log
        self.logger.info(
            "Profitability : Market {0}% | Crypto bot {1}%".format(market_delta * 100, total_profitability))

    @staticmethod
    def get_market_delta(market_data):
        market_begin = market_data[0][PriceIndexes.IND_PRICE_CLOSE.value]
        market_end = market_data[-1][PriceIndexes.IND_PRICE_CLOSE.value]

        if market_begin and market_end and market_begin > 0:
            market_delta = market_end / market_begin - 1 if market_end >= market_begin else market_end / market_begin - 1
        else:
            market_delta = 0

        return market_delta

    @staticmethod
    def enabled(config):
        return CONFIG_BACKTESTING in config and config[CONFIG_BACKTESTING][CONFIG_ENABLED_OPTION]

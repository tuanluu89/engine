from common.helper.config.utils import RunDate
from datetime import timedelta
from performance_backtest.constant.price_history import PRICE_HISTORY
import numpy as np

SNOTES_DEFAULT_TENOR = 90
SNOTES_DEFAULT_INTEREST = 2.8
SNOTES_DEFAULT_TAX = 0.05
SNOTES_DEFAULT_BET_UP_RATE = 0.5
SNOTES_DEFAULT_BET_DOWN_RATE = 1 - SNOTES_DEFAULT_BET_UP_RATE
SNOTES_TICKER = 'VN30_INDEX'

class SNotes:

    def __init__(self):
        self.order = []
        self.value = []
        pass

    # 02473040388
    def get_price(self, date_: RunDate, ticker):
        return list(filter(lambda price: price['date'] == date_, PRICE_HISTORY))[0][ticker]

    def _gen_order(self, start, end, maturity, amount, volume, interest, price):
        """

        :param start:
        :param end:
        :param maturity:
        :param amount:
        :param volume:
        :param interest:
        :param price:
        :return:
            [ dict(id=, start_date = '', end_date = '', maturity_date = '', amount = '', interest = '', vn30_index = ''
            ]
        """
        id = len(self.order) + 1
        start_date = start
        end_date = end
        maturity_date = start_date + timedelta(days=SNOTES_DEFAULT_TENOR)
        vn30_index = self.get_price(date_=start, ticker=SNOTES_TICKER)

        ## them cuoc xu huong nua, neu them cuoc xu huong o day thi se phai them phan S_ON, SSAVING, SBOND nua



    def filter_effective_order(self):
        pass

    def _check_renew(self):
        pass

    def _cal_rebalance(self):
        pass

    def _cal_value(self, date_):
        pass
from common.helper.config.utils import RunDate
from datetime import timedelta
import numpy as np

SON_TENOR = 1
SON_DEFAULT_INTEREST_RATE = 0.03
SON_MIN_INTEREST_RATE = 0.02
SON_MIN_INTEREST_CAP = 5e8
SON_DEFAULT_TAX = 0.05


class Son:

    def __init__(self, initial_amount, start_date: RunDate, ticker=None, tenor=SON_TENOR,
                 interest_rate=SON_DEFAULT_INTEREST_RATE):
        self.initial_amount = initial_amount
        self.start_date = start_date
        self.tenor = tenor
        self.interest_rate = interest_rate
        if self.initial_amount < SON_MIN_INTEREST_CAP:
            self.interest_rate = SON_MIN_INTEREST_RATE
        self.order = []
        self.value = []
        self.amount_not_allocated = [] ### TODO: đối với những coupon không reinvest đc do ko đủ phí sẽ chuyển vào book này.


    def _gen_order(self, start, end, maturity, amount, volume, interest, price):
        """
        Tại ngày đầu tiên self.start_date gen_order theo giá trị ban đầu + tenor mặc đinh
        tại ngày renew:
            terminate hợp đồng hiện hữu
        :return:
        """
        id = len(self.order)+1
        start_date = start
        end_date = end
        maturity_date = start_date + timedelta(days=SON_TENOR)
        amount = amount
        interest = SON_DEFAULT_INTEREST_RATE
        if amount < SON_MIN_INTEREST_CAP:
            interest = SON_MIN_INTEREST_RATE
        order = dict(id=id, start_date=start_date, end_date=end_date, maturity_date=maturity_date, amount=amount,
                     interest=interest)
        self.order.append(order)

    def _cal_rebalance(self, date_, rebalance_amount, rebalance_type):
        """
        rebalance son: chi can thuc hien update last order la done (vi hang ngay deu insert new order va update balance truoc roi)
        :param date_:
        :param rebalance_amount:
        :return:
        """
        self.order[-1]['amount'] += rebalance_amount
        pass

    def _check_renew(self, date_):
        """
        list all orders that are expired at date_
        :param date_:
        :return:
        added tax daily
        """
        # interest se dung None, vi trong ham gen_order co code xac dinh interest roi
        for i in np.arange(len(self.order)):
            if self.order[i]['end_date'] is None: # neu end_date = None
                if self.order[i]['maturity_date'] == date_:
                    # update end_date = date_
                    self.order[i]['end_date'] = date_
                    # add new order
                    new_order_amount = self.order[i]['amount'] * \
                                       (1 + self.order[i]['interest'] * (self.order[i]['end_date']-self.order[i]['start_date']).days/365 \
                                           * (1 - SON_DEFAULT_TAX)
                                        )
                    self._gen_order(start=date_, end=None, maturity=None, amount=new_order_amount,
                                    volume=None, interest=None, price=None)

    def _cal_value(self, date_):
        # với s-saving thì sẽ tạm tính trên lãi suất tất toán trước hạn
        # lý do: vì tại ngày tất toán đúng hạn (đáo hạn) thì đã có generate ra deal mới và trên deal đó thì số tiền đã được tính trên ls ban đầu
        filter_out_end_date_order = list(filter(lambda order: order['end_date'] is None, self.order))
        port_added_current_value = sum(i['amount'] for i in filter_out_end_date_order)
        self.value.append([date_, port_added_current_value])


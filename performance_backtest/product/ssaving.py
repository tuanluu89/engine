from common.helper.config.utils import RunDate
from datetime import timedelta
import numpy as np

SSAVING_DEFAULT_TENOR = 90
SSAVING_DEFAULT_INTEREST = 0.051
SSAVING_DEFAULT_TAX = 0.05
SSAVING_DEFAULT_PREWITHDRAW_LESS_THAN_30DAY_RATE = 0.002
SSAVING_DEFAULT_PREWITHDRAW_GREATER_THAN_30DAY_RATE = 0.03


class Ssaving:

    def __init__(self, initial_amount, start_date: RunDate, ticker=None, tenor=SSAVING_DEFAULT_TENOR,
                 interest_rate=SSAVING_DEFAULT_INTEREST):
        self.initial_amount = initial_amount
        self.start_date = start_date
        self.tenor = tenor
        self.interest_rate = interest_rate
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
        maturity_date = start_date + timedelta(days=SSAVING_DEFAULT_TENOR)
        amount = amount
        interest = SSAVING_DEFAULT_INTEREST
        # order = [id, start_date, end_date, maturity_date, amount, volume, interest, price]
        order = dict(id=id, start_date=start_date, end_date=end_date, maturity_date=maturity_date, amount=amount,
                     interest=interest)
        self.order.append(order)

    def _cal_rebalance(self, date_, rebalance_amount, rebalance_type):
        """
        neu rebalance_amount >0 thi gen_order moi
        neu rebalance_amount <0: tìm cách làm nào:
            1. filter nhung order con effective
        added tax to formula
        :param date_:
        :param rebalance_amount:
        :return:
        """
        if rebalance_amount > 0:
            self._gen_order(start=date_, end=None, maturity=None, amount=rebalance_amount,
                                    volume=None, interest=SSAVING_DEFAULT_INTEREST, price=None)
        else:
            effective_order = self.filter_effective_order()
            # update theo thu tu id cua giao dich giam dan (tuong duong can cu vao ngay start_date)
            i = len(effective_order) - 1
            while i >= 0:
                discounted_rate = 1 / ((
                        1 + (SSAVING_DEFAULT_PREWITHDRAW_LESS_THAN_30DAY_RATE if (date_ - effective_order[i]['start_date']).days < 30
                             else
                             SSAVING_DEFAULT_PREWITHDRAW_GREATER_THAN_30DAY_RATE) * (date_ - effective_order[i]['start_date']).days / 365
                )*(1-SSAVING_DEFAULT_TAX))
                discounted_rebalance_amount = rebalance_amount * discounted_rate
                if effective_order[i]['amount'] + discounted_rebalance_amount < 0:
                    # nếu amount + số tiền rebalance tính quy đổi về vẫn < 0 có nghĩa là cần rebalance tiếp
                    # 1. tính rebalance amount còn lại
                    rebalance_amount += effective_order[i]['amount'] / discounted_rate
                    # 2. update amount của order về 0
                    effective_order[i]['amount'] = 0
                else:
                    effective_order[i]['amount'] += discounted_rebalance_amount
                    rebalance_amount = 0  # rebalance du roi
                i -= 1

    def _check_renew(self, date_):
        """
        list all orders that are expired at date_
        added tax to formula
        :param date_:
        :return:
        """
        for i in np.arange(len(self.order)):
            if self.order[i]['end_date'] is None: # neu end_date = None
                if self.order[i]['maturity_date'] == date_:
                    # update end_date = date_
                    self.order[i]['end_date'] = date_
                    # add new order
                    new_order_amount = self.order[i]['amount'] * \
                                       (1 + self.order[i]['interest'] * (self.order[i]['end_date']-self.order[i]['start_date']).days/365 \
                                           * (1 - SSAVING_DEFAULT_TAX)
                                        )
                    # (self.order[i][2]-self.order[i][1])
                    # new order _amount = amount goc * (1 + ls * thoi gian / 365)
                        #TODO: trường hợp rebalance thì sẽ phải khác
                    self._gen_order(start=date_, end=None, maturity=None, amount=new_order_amount,
                                    volume=None, interest=SSAVING_DEFAULT_INTEREST, price=None)

    def filter_effective_order(self):
        """
        :return: eliminate order having end_date is not None
        """
        return list(filter(lambda order: order['end_date'] is None, self.order))

    def _cal_value(self, date_):
        # với s-saving thì sẽ tạm tính trên lãi suất tất toán trước hạn
        # lý do: vì tại ngày tất toán đúng hạn (đáo hạn) thì đã có generate ra deal mới và trên deal đó thì số tiền đã được tính trên ls ban đầu

        # effective_order = list(filter(lambda order: order[2] is None, self.order))
        # update 2022-08-25: thay lai suat tat toan truoc han bang dung lai suat hop dong
        # SSAVING_DEFAULT_PREWITHDRAW_LESS_THAN_30DAY_RATE
        #                                             if (date_-i[1]).days < 30 else
        #                                             SSAVING_DEFAULT_PREWITHDRAW_GREATER_THAN_30DAY_RATE
        port_added_current_value = sum(i['amount'] * (1 + i['interest'] *
                                               (date_ - i['start_date']).days / 365) for i in self.filter_effective_order())
        self.value.append([date_, port_added_current_value])


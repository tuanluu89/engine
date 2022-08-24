from common.helper.config.utils import RunDate
from datetime import timedelta
import numpy as np

SSAVING_DEFAULT_TENOR = 90
SSAVING_DEFAULT_INTEREST = 0.051
SSAVING_DEFAULT_TAX = 0.05
SSAVING_DEFAULT_PREWITHDRAW_LESS_THAN_30DAY_RATE = 0.002
SSAVING_DEFAULT_PREWITHDRAW_GREATER_THAN_30DAY_RATE = 0.03

contract_type = dict(
    id=1,
    start_date=1,
    end_date=2,
    maturity_date=3,
    amount=4,
    interest_rate=5,
)


class Ssaving:

    def __init__(self, initial_amount, start_date: RunDate, ticker=None, tenor=SSAVING_DEFAULT_TENOR,
                 interest_rate=SSAVING_DEFAULT_INTEREST):
        self.initial_amount = initial_amount
        self.start_date = start_date
        self.tenor = tenor
        self.interest_rate = interest_rate
        self.order = []
        self.value = []
        pass

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
        volume = volume
        interest = SSAVING_DEFAULT_INTEREST
        price = price
        order = [id, start_date, end_date, maturity_date, amount, volume, interest, price]
        self.order.append(order)

    def _check_renew(self, date_):
        """
        :param date_:
        :return:
        """
        for i in np.arange(len(self.order)):
            if self.order[i][2] is None: # neu end_date = None
                if self.order[i][3] == date_:
                    # update end_date = date_
                    self.order[i][2] = date_
                    # add new order
                    new_order_amount = self.order[i][4] * (1 + self.order[i][6] * (self.order[i][2]-self.order[i][1]).days/365) # (self.order[i][2]-self.order[i][1])
                    # new order _amount = amount goc * (1 + ls * thoi gian / 365)
                        #TODO: trường hợp rebalance thì sẽ phải khác
                    self._gen_order(start=date_, end=None, maturity=None, amount=new_order_amount,
                                    volume=None, interest=SSAVING_DEFAULT_INTEREST, price=None)

    def _cal_value(self, date_):
        # với s-saving thì sẽ tạm tính trên lãi suất tất toán trước hạn
        # lý do: vì tại ngày tất toán đúng hạn (đáo hạn) thì đã có generate ra deal mới và trên deal đó thì số tiền đã được tính trên ls ban đầu
        temp_value = 0.0
        for i in np.arange(len(self.order)):
            filter_out_end_date_order = list(filter(lambda order: order[2] is None, self.order))
            port_added_current_value = sum(i[4] * (1 + (SSAVING_DEFAULT_PREWITHDRAW_LESS_THAN_30DAY_RATE if (date_-i[1]).days < 30 else
                                                        SSAVING_DEFAULT_PREWITHDRAW_GREATER_THAN_30DAY_RATE)
                                                         *
                                                   (date_ - i[1]).days / 365) for i in filter_out_end_date_order)
            self.value.append([date_, port_added_current_value])
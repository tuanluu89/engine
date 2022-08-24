from common.helper.config.utils import RunDate
from datetime import timedelta

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


    def print_test(self):
        print(1)

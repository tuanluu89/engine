from performance_backtest.product.ssaving import Ssaving
from common.helper.config.utils import RunDate, date_range
import numpy as np


class MasterPortfolio:
    """
        MasterPortfolio : there are many product (sub_portfolio) inside masterportfolio
        Everyday we load BOP (=EOP of yesterday) and then check whether we will rebalance masterportfolio or not.

    """
    def __init__(self, start_date: RunDate,
                 end_date: RunDate,
                 initial_amount,
                 product_list,
                 rebalance_option
                 ):
        self.start_date = start_date
        self.end_date = end_date
        self.date_range = date_range(start=start_date, end=end_date)
        self.initial_amount = initial_amount
        self.rebalance_option = rebalance_option
        self.product_list = product_list
        self.portfolio = []

    def create_object(self, product_class, start_date: RunDate, initial_amount):
        """
        for each product in product_list, we will create object (based on their product_class)
        :param product_class:
        :param start_date:
        :param initial_amount:
        :return:
        """
        if product_class == 'ssaving':
            return Ssaving(start_date=start_date, initial_amount=initial_amount)

    def allocate(self):
        """
            at first, we allocate initial_amount to each product (in product_list, sub_portfolio) based on their weight
        :return:
        """
        for i in np.arange(len(self.product_list)):
            portfolio_i = self.create_object(
                product_class=self.product_list[i]['product_class'],
                start_date=self.start_date,
                initial_amount=self.initial_amount * self.product_list[i]['weight']
            )
            self.portfolio.append(portfolio_i)

    def run(self):
        # for i = self.start_date to end_date
            # check xem có phải ngày thực hiện rebalance hay không
            # nếu là ngày rebalance:
                # calculate portfolio value của ngày liền trước => tính ra portfolio value tại đầu ngày i
                    # =>call function reblance cho từng portfolio
        # calculate portfolio value
        for i in np.arange(len(self.date_range)):
            # print(self.date_range[i])
            if i == 0:
                self.allocate()
                for u in np.arange(len(self.product_list)):
                    self.portfolio[u]._gen_order(start=self.start_date, end=None, maturity=None,
                                                 amount=self.portfolio[u].initial_amount,
                                                 volume=None,
                                                 interest=None,
                                                 price=None)
        # pass

### testing
from common.helper.config import config
from datetime import timedelta
start_date = config.run_date - timedelta(days=180)
end_date = config.run_date - timedelta(days=170)
product_list = [
    dict(id=1, product_class='ssaving', weight=0.3),
    dict(id=2, product_class='ssaving', weight=0.7)
]
master_portfolio = MasterPortfolio(start_date=start_date, end_date=end_date, initial_amount=1e9,
                                   rebalance_option=None,
                                   product_list=product_list
                                   )
master_portfolio.run()

from performance_backtest.product.ssaving import Ssaving
from performance_backtest.product.son import Son
from performance_backtest.product.sbond import SBond
from common.helper.config.utils import RunDate, date_range
from performance_backtest.constant.rebalance import generate_rebalance_date_range, EQUITY_IN_SIGNAL, EQUITY_OUT_SIGNAL
import numpy as np

REBALANCE_DATE_RANGE = generate_rebalance_date_range()
REBALANCE_TYPE = [1, 2] # 1: Rebalance with equity signal in, 2: rebalance with equity signal out

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
        self.total_value = []
        self.total_amount_not_allocated = 0.0

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
        if product_class == 'son':
            return Son(start_date=start_date, initial_amount=initial_amount)
        if product_class == 'sbond':
            return SBond(start_date=start_date, initial_amount=initial_amount)

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

    @staticmethod
    def get_rebalance_type(date_: RunDate):
        """ check xem ngày báo cáo có là ngày rebalance hay không
        :param date_: ngày báo cáo
        :return: rebalance_type:
            0: không rebalance
            1: rebalance theo hướng equity in
            2: rebalance theo hướng equity out
        """
        filter_rebalance_range = list(
            filter(lambda rebalance_range: rebalance_range['date'] == date_, REBALANCE_DATE_RANGE)
        )
        if not filter_rebalance_range:
            return 0
        else:
            return filter_rebalance_range[0]['rebalance_type']

    def run(self):
        # for i = self.start_date to end_date
            # check xem có phải ngày thực hiện rebalance hay không
            # nếu là ngày rebalance:
                # calculate portfolio value của ngày liền trước => tính ra portfolio value tại đầu ngày i
                    # =>call function reblance cho từng portfolio
        # calculate portfolio value
        for i in np.arange(len(self.date_range)):
            # b1 neu la ngay dau tien thi allocate portfolio rui gen_order
            date_ = self.date_range[i]
            if i == 0:
                self.allocate()
                for product in np.arange(len(self.product_list)):
                    self.portfolio[product]._gen_order(start=self.start_date, end=None, maturity=None,
                                                 amount=self.portfolio[product].initial_amount,
                                                 volume=None,
                                                 interest=None,
                                                 price=None)

            temp_total_portfolio_value = 0.0
            for product in np.arange(len(self.product_list)):
                # check renew
                self.portfolio[product]._check_renew(date_=date_)
                # check rebalance
                rebalance_type = MasterPortfolio.get_rebalance_type(date_=date_)
                if rebalance_type in REBALANCE_TYPE:
                    ytd_designed_product_value = 0.0 # khoi tao value
                    if rebalance_type == EQUITY_IN_SIGNAL:
                        ytd_designed_product_value = (self.total_value[-1][1] + self.total_amount_not_allocated) * \
                                                     self.product_list[product]['weight']
                    if rebalance_type == EQUITY_OUT_SIGNAL:
                        ytd_designed_product_value = (self.total_value[-1][1] + self.total_amount_not_allocated) * \
                                                     self.product_list[product]['weight_on_equity_signal_out']
                    self.total_amount_not_allocated = 0.0
                    ytd_actual_product_value = self.portfolio[product].value[-1][1] #can cu vao gia tri portfolio ngay gan nhat
                    self.portfolio[product]._cal_rebalance(
                        date_=date_, rebalance_amount=ytd_designed_product_value - ytd_actual_product_value,
                        rebalance_type = rebalance_type
                    )
                self.portfolio[product]._cal_value(date_=date_)
                temp_total_portfolio_value += self.portfolio[product].value[-1][1]
                ### TODO: add thêm amount not allocated:
                if len(self.portfolio[product].amount_not_allocated) > 0:
                    if self.portfolio[product].amount_not_allocated[-1]['start_date'] == date_:
                        self.total_amount_not_allocated += self.portfolio[product].amount_not_allocated[-1]['amount']
            self.total_value.append([date_, temp_total_portfolio_value])


import pandas as pd

start_date = RunDate('2017-03-01')
end_date = RunDate('2018-01-03')

product_list = [
    dict(id=1, product_class='ssaving', weight=0.3, weight_on_equity_signal_out=0.2),
    dict(id=2, product_class='son', weight=0.2, weight_on_equity_signal_out=0.3),
    dict(id=3, product_class='sbond', weight=0.5, weight_on_equity_signal_out=0.5)
]
master_portfolio = MasterPortfolio(start_date=start_date, end_date=end_date, initial_amount=1e9,
                                   rebalance_option=None,
                                   product_list=product_list
                                   )
master_portfolio.run()

master_portfolio_df = pd.DataFrame(master_portfolio.total_value, columns=['date', 'total_value'])
port1_df = pd.DataFrame(master_portfolio.portfolio[0].value, columns=['date', 'port1_value'])
port2_df = pd.DataFrame(master_portfolio.portfolio[1].value, columns=['date', 'port2_value'])
port3_df = pd.DataFrame(master_portfolio.portfolio[2].value, columns=['date', 'port3_value'])

port1_df['date'] = port1_df['date'].apply(lambda x: x.to_date().strftime('%Y%m%d'))
port2_df['date'] = port2_df['date'].apply(lambda x: x.to_date().strftime('%Y%m%d'))
port3_df['date'] = port3_df['date'].apply(lambda x: x.to_date().strftime('%Y%m%d'))
master_portfolio_df['date'] = master_portfolio_df['date'].apply(lambda x: x.to_date().strftime('%Y%m%d'))

port1_port2_df = pd.merge(port1_df, port2_df, on='date')
port1_2_3_df = pd.merge(port1_port2_df, port3_df, on='date')

df = pd.merge(port1_2_3_df, master_portfolio_df, on='date')
df.to_excel('test_sbond_v3_rebalance_type.xlsx', index=False)

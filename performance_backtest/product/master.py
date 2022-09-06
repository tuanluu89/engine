from performance_backtest.product.ssaving import Ssaving
from performance_backtest.product.son import Son
from performance_backtest.product.sbond import SBond
from common.helper.config.utils import RunDate, date_range
from performance_backtest.constant.rebalance import generate_rebalance_date_range
import numpy as np

REBALANCE_DATE_RANGE = generate_rebalance_date_range()


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

    def run(self):
        # for i = self.start_date to end_date
            # check xem có phải ngày thực hiện rebalance hay không
            # nếu là ngày rebalance:
                # calculate portfolio value của ngày liền trước => tính ra portfolio value tại đầu ngày i
                    # =>call function reblance cho từng portfolio
        # calculate portfolio value
        for i in np.arange(len(self.date_range)):
            # print(self.date_range[i])
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
            # neu khong phai la ngay dau tien thi check renew
            # sau khi check renew (bao gom ca viec generate order moi)
            # check xem ngay date_ co phai rebalance_date ko:
                # neu la rebalance_date thi se thuc hien: tinh toan xem can tang hay giam gia tri cua tung portfolio dua
                # tren gia tri tong portfolio ngay hom trc
            temp_total_portfolio_value = 0.0
            for product in np.arange(len(self.product_list)):
                self.portfolio[product]._check_renew(date_=date_)
                if date_ in REBALANCE_DATE_RANGE:
                    ytd_designed_product_value = (self.total_value[-1][1] + self.total_amount_not_allocated) * \
                                                 self.product_list[product]['weight']
                    self.total_amount_not_allocated = 0.0# sau khi rebalance thì giá trị này chuyển về 0
                    ytd_actual_product_value = self.portfolio[product].value[-1][1]
                    self.portfolio[product]._cal_rebalance(
                        date_=date_, rebalance_amount=ytd_designed_product_value - ytd_actual_product_value)
                self.portfolio[product]._cal_value(date_=date_)
                temp_total_portfolio_value += self.portfolio[product].value[-1][1]
                ### TODO: add thêm amount not allocated:
                if len(self.portfolio[product].amount_not_allocated) > 0:
                    if self.portfolio[product].amount_not_allocated[-1]['start_date'] == date_:
                        self.total_amount_not_allocated += self.portfolio[product].amount_not_allocated[-1]['amount']
            self.total_value.append([date_, temp_total_portfolio_value])

### testing
from common.helper.config import config
from datetime import timedelta
import pandas as pd
# start_date = config.run_date - timedelta(days=360)
# end_date = config.run_date - timedelta(days=1)
# end_date = start_date + timedelta(days=180)

start_date = RunDate('2017-03-01')
end_date = RunDate('2018-01-03')

product_list = [
    dict(id=1, product_class='ssaving', weight=0.3),
    dict(id=2, product_class='son', weight=0.2),
    dict(id=3, product_class='sbond', weight=0.5)
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
df.to_excel('test_sbond_v2_rebalance.xlsx', index=False)

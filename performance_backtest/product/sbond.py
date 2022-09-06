from common.helper.config.utils import RunDate
from datetime import timedelta
import numpy as np

from performance_backtest.constant.bond_info import BondInfo

SBOND_DEFAULT_COUPON_TAX = 0.05
SBOND_DEFAULT_SELLING_TAX = 0.001
TRANSACTION_FEE_RATE = 0.002 # 0.2% MỆNH GIÁ, TỐI THIỂU 200K, TỐI ĐA 10 TR
TRANSACTION_FEE_MIN = 200000
TRANSACTION_FEE_MAX = 10000000


class SBond:

    def __init__(self, initial_amount, start_date: RunDate):
        self.initial_amount = initial_amount
        self.start_date = start_date
        self.order = []
        self.value = []
        self.amount_not_allocated = [] ### TODO: đối với những coupon không reinvest đc do ko đủ phí sẽ chuyển vào book này.
        self.bond_statistics = BondInfo.bond_statistics
        self.bond_coupon = BondInfo.bond_coupon
        self.bond_price = BondInfo.bond_price

    def _filter_available_bond(self, date_: RunDate):
        """
        :param date_:
        :return: get bond available at the selected {date_}, sorted by maturity date (
        the last maturity bond will be selected)
        output dict(id=1, bond_code='ABC', start_date = {}, maturity_date={})
        """
        return list(filter(lambda bond: (bond['start_date'] <= date_) & (bond['maturity_date'] > date_),
                           self.bond_statistics))

    def _cal_transaction_fee(self, par_value):
        transaction_fee = par_value * TRANSACTION_FEE_RATE
        if transaction_fee < TRANSACTION_FEE_MIN:
            transaction_fee = TRANSACTION_FEE_MIN
        if transaction_fee > TRANSACTION_FEE_MAX:
            transaction_fee = TRANSACTION_FEE_MAX
        return transaction_fee

    def _get_bond_info_by_id(self, bond_id):
        """
        output schema = dict(id={}, bond_code={}, start_date={}, maturity_date={})
        :param bond_id:
        :return:
        """
        return list(filter(lambda bond: bond['id'] == bond_id, self.bond_statistics))[0]

    @staticmethod
    def _get_last_maturity_bond(available_bond):
        """
        output dict(id=1, bond_code='ABC', start_date = {}, maturity_date={})
        :param available_bond: list of all available bond, which will be sorted by maturity_date asc
        :return: get last maturity date by get last element of the list
        """
        return sorted(available_bond, key=lambda bond: bond['maturity_date'])[-1]

    def _get_bond_price(self, bond_id, date_: RunDate):
        """
        first: get all price with date <= date_
        then get the last one
        output schema dict(buying_price={}, selling_price={})
        """
        price_prior_to_date = list(filter(lambda bond: (bond['bond_id'] == bond_id) & (bond['date'] <= date_),
                                          self.bond_price))
        last_available_price = sorted(price_prior_to_date, key=lambda bond: bond['date'])[-1]
        return dict(buying_price=last_available_price['buying_price'],
                    selling_price=last_available_price['selling_price'])

    def _gen_amount_not_allocated(self, start_date: RunDate, amount):
        if len(self.amount_not_allocated) > 0:
            current_amount_not_allocated = list(filter(lambda order: order['start_date'] == start_date,
                                                       self.amount_not_allocated))
            if len(current_amount_not_allocated) > 0: #nếu đã có 1 order cho ngày start_date thì sẽ update amount
                current_amount_not_allocated[0]['amount'] += amount
            else: # nếu chưa có order nào thì gen 1 order mới với id + 1
                amount_not_allocated_id = len(self.amount_not_allocated) + 1
                self.amount_not_allocated.append(dict(id=amount_not_allocated_id, start_date=start_date, amount=amount))
        else: # gen order với id = 1
            self.amount_not_allocated.append(dict(id=1, start_date=start_date, amount=amount))

    def _gen_order(self, start, end, maturity, amount, volume, interest, price):
        """
            1. listed all available bond by {start}
            2. get last maturity bond
            trường hợp ko gen đc order do số tiền < thuế/phí tối thiểu thì sẽ đẩy sang mục amount_not_allocated và
            gen order khi rebalance toàn danh mục
        :return: output schema = dict(id, start_date, end_date, maturity_date, amount, bond_id, quantity, buying_price)
        """
        available_bond = self._filter_available_bond(date_=start)
        last_maturity_bond = self._get_last_maturity_bond(available_bond=available_bond)
        bond_id = last_maturity_bond['id']

        id = len(self.order) + 1
        start_date = start
        end_date = end
        maturity_date = last_maturity_bond['maturity_date']
        buying_price = self._get_bond_price(bond_id=bond_id, date_=start_date)['buying_price']
        quantity = amount/buying_price
        par_value = quantity * last_maturity_bond['par_value']
        transaction_fee = self._cal_transaction_fee(par_value=par_value)
        amount_after_fee = amount-transaction_fee
        quantity_after_fee = amount_after_fee/buying_price
        # order = [id, start_date, end_date, maturity_date, amount, volume, bond_id, buying_price]
        if amount_after_fee > 0:
            order = dict(id=id, start_date=start_date, end_date=end_date, maturity_date=maturity_date, amount=amount_after_fee,
                         quantity=quantity_after_fee, bond_id=bond_id, buying_price=buying_price)
            self.order.append(order)
        else:
            self._gen_amount_not_allocated(start_date=start, amount=amount)

    def _cal_rebalance(self, date_, rebalance_amount):
        """
        :param rebalance_amount: số tiền cần tăng/giảm ở value của danh mục tại cuối ngày rebalance
        Trường hợp rebalance_amount >0: insert thêm order
        Trường hợp rebalance_amount <0: bán bớt số lượng và update quantity/amount, lưu ý giá bán và thuế bán, phí bán
        Trường hợp rebalance_amount ko đủ để mua thêm trái phiếu --> sửa lại phần check_renew
        :return:
        """
        if rebalance_amount > 0:
            #_gen_order(self, start, end, maturity, amount, volume, interest, price):
            self._gen_order(start=date_, end=None, maturity=None, amount=rebalance_amount,
                            volume=None, interest=None, price=None)
        else:
            effective_order = self.filter_effective_order()
            i = len(effective_order) - 1
            while i >= 0:
                mark_to_market_value = effective_order[i]['quantity'] * self._get_bond_price(
                    bond_id=effective_order[i]['bond_id'], date_=date_
                )['selling_price']
                if mark_to_market_value + rebalance_amount < 0:
                    effective_order[i]['end_date'] = date_
                    effective_order[i]['amount'] = 0.0
                    effective_order[i]['quantity'] = 0.0
                    rebalance_amount += mark_to_market_value
                else:
                    rebalance_rate = 1 + rebalance_amount / mark_to_market_value
                    effective_order[i]['amount'] *= rebalance_rate
                    effective_order[i]['quantity'] *= rebalance_rate
                    rebalance_amount = 0.0
                i -= 1

    def filter_effective_order(self):
        return list(filter(lambda order: order['end_date'] is None, self.order))

    def get_bond_coupon(self, bond_id, start_date, end_date, date_):
        """
        :param bond_id:
        :param start_date: ngày mua trái phiếu
        :param date_: liệt kê danh sách nhận coupon cho mã bond_id tại ngày date_ và thỏa mãn mua trái phiếu
            không muộn hơn ngày giao dịch không hưởng quyền

        :return: sum coupon_rate: của những coupon mà ngày trả coupon vào đúng ngày date_
        # 2022-08-30: update thêm ý kiến của a Thông: từ ngày chốt quyền -> coupon tính luôn vào giá trị của danh mục
        #      => chuyển từ ngày trả coupon sang ngày chốt quyền
        """
        bond_coupon_by_bond_id = list(
            filter(lambda bond_coupon: bond_coupon['bond_id'] == bond_id, self.bond_coupon)
        )
        if end_date is None:
            bond_coupon_after_start_date_and_before_end_date = list(
                filter(lambda bond_coupon: bond_coupon['coupon_expiration_date'] >= start_date
                       , bond_coupon_by_bond_id)
        )
        else:
            bond_coupon_after_start_date_and_before_end_date = list(
                filter(lambda bond_coupon: (bond_coupon['coupon_expiration_date'] >= start_date) &
                                           (bond_coupon['coupon_expiration_date'] < end_date)
                       , bond_coupon_by_bond_id)
        )

        coupon_list = list(
            filter(lambda bond_coupon: bond_coupon['coupon_expiration_date'] == date_, #coupon_date
                   bond_coupon_after_start_date_and_before_end_date)
        )
        if len(coupon_list) > 0:
            return sum(i['coupon_rate'] for i in coupon_list)/100.00
        else:
            return 0

    def _check_renew(self, date_):
        """
        :param date_:
        :return: liệt kê tất cả giao dịch có ngày đáo hạn = ngày date_ và tất cả giao dịch được hưởng coupon vào ngày date_
        """
        # effective_order = self.filter_effective_order()
        for order in self.order:
            sum_coupon_rate = self.get_bond_coupon(bond_id=order['bond_id'], start_date=order['start_date'],
                                                   end_date=order['end_date'], date_=date_) * \
                              (1 - SBOND_DEFAULT_COUPON_TAX)
            bond_stats = self._get_bond_info_by_id(bond_id=order['bond_id'])
            par_value = bond_stats['par_value']
            if sum_coupon_rate > 0:
                sum_coupon = sum_coupon_rate * par_value * order['quantity']
            else:
                sum_coupon = 0
            if (order['maturity_date'] == date_) & (order['end_date'] is None):
                maturity_amount = order['quantity'] * par_value
                order['end_date'] = date_
            else:
                maturity_amount = 0
            if sum_coupon + maturity_amount > 0:
                new_order_amount = sum_coupon+maturity_amount
                self._gen_order(start=date_, end=None, maturity=None, amount=new_order_amount, volume=None, interest=None, price=None)

    def _cal_value(self, date_):
        # list effective order
        # get selling price for each order
        """
        :param date_:
        :return:
        issue: trong khoảng thời gian từ thời điểm giao dịch không hưởng quyền --> ngày thực hiện trả coupon,

        TODO: cần check xem với những trái phiếu của SSi khi định giá trong những ngày này đã loại trừ coupon ra chưa,
        """
        effective_order = self.filter_effective_order()
        self.value.append([date_,
                           sum(i['quantity'] * self._get_bond_price(bond_id=i['bond_id'], date_=date_)['selling_price']
                               for i in effective_order)])

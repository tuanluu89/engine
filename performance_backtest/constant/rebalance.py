from common.helper.config.utils import RunDate
from common.helper.config import config
from datetime import timedelta

def generate_rebalance_date_range():
    # start_date = RunDate('2017-01-01')
    # rebalance_date_range = []
    # while start_date <= config.run_date:
    #     rebalance_date_range.append(start_date)
    #     start_date = start_date + timedelta (days=30)
    # return rebalance_date_range
    return [RunDate('2017-06-17'), RunDate('2017-12-15')]
    # return []
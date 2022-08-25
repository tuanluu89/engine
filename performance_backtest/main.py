# from common.helper.config import config
#
# run_date = config.run_date
order = [order1.copy(), order1.copy(), order1.copy()]
order[1][0] = 8
order[1][1] = RunDate('2022-03-10')
order[1][3] = RunDate('2022-04-09')
order[1][4] = 1e8
order[2][0] = 9
order[2][1] = RunDate('2022-03-15')
order[2][3] = RunDate('2022-04-14')
order[2][4] = 120e6
date_ = RunDate('2022-03-24')
rebalance_amount = -300e6
for o in order:
    print(o)
i = len(order) - 1

while i >= 0:
    print(f"""
    Số tiền cần rebalance {rebalance_amount}
    order ban đầu {order[i]}
""")
    discounted_rate = 1/(
            1 + (SSAVING_DEFAULT_PREWITHDRAW_LESS_THAN_30DAY_RATE if (date_ - order[i][1]).days < 30
                 else
                 SSAVING_DEFAULT_PREWITHDRAW_GREATER_THAN_30DAY_RATE) * (date_ - order[i][1]).days / 365
    )
    discounted_rebalance_amount = rebalance_amount * discounted_rate
    if order[i][4] + discounted_rebalance_amount < 0:
        # nếu amount + số tiền rebalance tính quy đổi về vẫn < 0 có nghĩa là cần rebalance tiếp
        # 1. tính rebalance amount còn lại
        rebalance_amount += order[i][4] / discounted_rate
        # 2. update amount của order về 0
        order[i][4] = 0
    else:
        order[i][4] += discounted_rebalance_amount
        rebalance_amount = 0  # rebalance du roi
    print(f"""
    after rebalance :
    số tiền còn lại cần rebalance cho lần tiếp theo {rebalance_amount}
    order sau khi rebalance: {order[i]}
""")
    i -= 1
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime

import backtrader as bt

import models.commissions.mycommission as my_commission

import models.strategy.strategy_my01 as my_strategy

import akshare as ak

import qstock as qs

# 初期资产
cash = 200000
symbol = "zz800"

if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # 初始资金设置
    cerebro.broker.setcash(cash)

    # 万五的手续费
    commission = my_commission.MyCommission(commission=0.05)  # 0.05%
    cerebro.broker.addcommissioninfo(commission)

    # 每批最少100股
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    # index_stock_cons_csindex_df = ak.index_stock_cons_csindex(symbol=symbol)

    index_stock_cons_csindex_df = qs.index_member(symbol)

    for _, stock in index_stock_cons_csindex_df.iterrows():
        file = "./data/day/" + stock['股票代码'] + ".csv"
        data = bt.feeds.GenericCSVData(
            dataname=file,
            fromdate=datetime.datetime(2023, 1, 1),
            nullvalue=0.0,
            dtformat=('%Y-%m-%d'),
            datetime=0,
            open=1,
            close=2,
            high=3,
            low=4,
            volume=5,
            openinterest=-1
        )
        cerebro.adddata(data, name=stock['股票代码'])

    cerebro.addstrategy(my_strategy.MyStrategy01)

    print('回测开始，资产价值: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    print('回测完成，资产价值: %.2f' % cerebro.broker.getvalue())

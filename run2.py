from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime

import backtrader as bt

import models.commissions.mycommission as my_commission

import models.strategy.strategy_my01 as my_strategy

import models.strategy.strategy_big_small_rotate as strategy_big_small_rotate

import akshare as ak

import qstock as qs

import os

# 初期资产
cash = 200000

if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # 初始资金设置
    cerebro.broker.setcash(cash)

    # 万五的手续费
    commission = my_commission.MyCommission(commission=0.05)  # 0.05%
    cerebro.broker.addcommissioninfo(commission)

    # 每次都是全仓
    cerebro.addsizer(bt.sizers.AllInSizerInt, percents=95)

    # index_stock_cons_csindex_df = ak.index_stock_cons_csindex(symbol=symbol)

    index_stock_cons_csindex_df = ['510050', '159949']

    for stock in index_stock_cons_csindex_df:
        file = "./data/day/" + stock + ".csv"

        if not os.path.isfile(file):
            print(file + " 文件不存在")
            continue

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
        cerebro.adddata(data, name=stock)

    cerebro.addstrategy(strategy_big_small_rotate.StrategyBigSmallRotate)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe')

    print('回测开始，资产价值: %.2f' % cerebro.broker.getvalue())

    thestrats = cerebro.run()
    thestrat = thestrats[0]

    print('回测完成，资产价值: %.2f' % cerebro.broker.getvalue())

    print('Sharpe Ratio:', thestrat.analyzers.mysharpe.get_analysis())

    cerebro.plot()

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt

import akshare as ak

import pandas as pd

from datetime import datetime


def datafeeds(code='000001'):
    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20220101",
                                            adjust="qfq").iloc[:, :6]
    # 转换成bt需要的数据格式
    stock_zh_a_hist_df.columns = [
        'date',
        'open',
        'close',
        'high',
        'low',
        'volume',
    ]

    stock_zh_a_hist_df.index = pd.to_datetime(stock_zh_a_hist_df['date'])
    # print(stock_zh_a_hist_df)
    # start_date = datetime(2022, 1, 1)  # 回测开始时间
    # end_date = datetime(2023, 6, 5)  # 回测结束时间

    data = bt.feeds.PandasData(dataname=stock_zh_a_hist_df)

    return data


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('exitbars', 5),
        ('maperiod', 15),
    )

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.sma = dict()
        for data in self.datas:
            self.sma[data._name] = bt.indicators.SimpleMovingAverage(
                data, period=self.params.maperiod)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY %s EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.data._name, order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL %s EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.data._name, order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('毛收益 %0.2f, 扣佣后收益 % 0.2f, 佣金 %.2f, 市值 %.2f, 现金 %.2f' %
                 (trade.pnl, trade.pnlcomm, trade.commission, self.broker.getvalue(), self.broker.getcash()))

    def notify_data(self, data, status, *args, **kwargs):
        dn = data._name
        dt = datetime.now()
        msg = 'Data Status: {}'.format(data._getstatusname(status))
        print(dt, dn, msg)

    def next(self):
        for data in self.datas:
            self.log('Close %s, %.2f' % (data._name, data.close[0]))
            # 获取仓位
            pos = self.getposition(data).size
            if not pos:
                if data.close[0] > self.sma[data._name][0]:
                    self.log('BUY %s CREATE, %.2f' % (data._name, data.close[0]))
                    self.order = self.buy(data=data)
            else:
                if data.close[0] < self.sma[data._name][0]:
                    self.log('SELL %s CREATE, %.2f' % (data._name, data.close[0]))
                    self.order = self.close(data=data)


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    bt.SignalStrategy

    # 修改初始资金
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)

    # 获取数据
    data = datafeeds('000001')
    cerebro.adddata(data, name='000001')

    data = datafeeds('000002')
    cerebro.adddata(data, name='000002')

    # Add a strategy
    cerebro.addstrategy(TestStrategy, exitbars=5)

    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot()

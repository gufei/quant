import backtrader as bt
import datetime
import redis
import sys
import os

sys.path.append(os.path.dirname(sys.path[0]))
import utils.notify as notify


# https://mp.weixin.qq.com/s/g8TyAWZABtOc8Ir6vWe18Q
# 大小盘轮动策略
class StrategyBigSmallRotate(bt.Strategy):
    params = dict(period=21)

    def log(self, txt, dt=None):
        """Logging function for this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def sendmsg(self, type="买入", data=None):
        if not data:
            return
        if self.date_now.strftime('%Y-%m-%d') == data.datetime.date(0).strftime('%Y-%m-%d'):
            msg = "轮动策略运行报告\n"
            msg += "日期：" + data.datetime.date(0).strftime('%Y-%m-%d') + "\n"
            msg += "标的：" + data._name + "\n"
            msg += "价格：%.2f" % data.lines.close[0] + "\n"
            msg += "方向：" + type

            notify.send_msg_by_redis("stock", msg)

    def __init__(self):
        self.sma = dict()
        self.stock_data = dict()
        self.rateOfChange100 = list(range(len(self.datas)))

        self.date_now = datetime.datetime.now()

        for index, data in enumerate(self.datas):
            self.rateOfChange100[index] = bt.indicators.RateOfChange100(data, period=self.params.period)

        # self.buy_signal = list(range(len(self.datas)))
        # for index, data in enumerate(self.datas):
        #     self.buy_signal[index] = bt.And(self.rateOfChange100[0] > 0,
        #                                     self.rateOfChange100[0] > self.rateOfChange100[1])
        #
        #
        # self.close_signal = bt.And(self.rateOfChange100[0] < 0, self.rateOfChange100[1] < 0)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    '买入 %s 执行成功, 单价: %.2f, 总金额: %.2f, 手续费 %.2f' %
                    (order.data._name, order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('卖出 %s 执行成功, 单价: %.2f, 总金额: %.2f, 手续费 %.2f' %
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

    def next(self):
        pos = list(range(len(self.datas)))
        for index, data in enumerate(self.datas):
            pos[index] = self.getposition(data)

        if self.rateOfChange100[0] < 0 and self.rateOfChange100[1] < 0:
            for index, data in enumerate(self.datas):
                if pos[index].size:
                    self.sendmsg(type="卖出", data=data)
                    self.close(data=data)
            return

        if self.rateOfChange100[0] > 0 and self.rateOfChange100[0] > self.rateOfChange100[1]:
            if pos[0].size:
                return
            elif pos[1].size:
                self.close(data=self.datas[1])
                self.sendmsg(type="卖出", data=self.datas[1])
                return
            else:
                self.buy(data=self.datas[0])
                self.sendmsg(type="买入", data=self.datas[0])
                return

        if self.rateOfChange100[1] > 0 and self.rateOfChange100[1] > self.rateOfChange100[0]:
            if pos[1].size:
                return
            elif pos[0].size:
                self.close(data=self.datas[0])
                self.sendmsg(type="卖出", data=self.datas[0])
                return
            else:
                self.buy(data=self.datas[1])
                self.sendmsg(type="买入", data=self.datas[1])
                return

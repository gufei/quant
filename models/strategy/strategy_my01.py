import backtrader as bt
import datetime
import sys
import os

sys.path.append(os.path.dirname(sys.path[0]))
import utils.notify as notify


# 30天涨幅超过20%，并且在最近10天维持6%箱体振荡
class MyStrategy01(bt.Strategy):

    def log(self, txt, dt=None):
        """Logging function for this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def sendmsg(self, data=None):
        if not data:
            return

        msg = self.__class__.__name__ + " 策略运行报告\n"
        msg += "日期：" + self.datas[0].datetime.date(0).isoformat() + "\n"
        msg += "标的：" + data._name + "\n"
        msg += "价格：%.2f" % data.lines.close[0] + "\n"
        msg += "符合购买条件，请人工审核后处理"

        notify.send_msg_by_redis("stock", msg)

    def __init__(self):
        self.date_now = datetime.datetime.now().strftime('%Y-%m-%d')

        self.sma = dict()
        for data in self.datas:
            self.sma[data._name] = bt.indicators.SimpleMovingAverage(
                data, period=10)

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

        if self.date_now != self.datas[0].datetime.date(0):
            return

        for data in self.datas:
            # 获得相关持仓
            pos = self.getposition(data)
            if not pos.size:
                # 至少有31天的数据
                if len(data.lines.close.get(size=31)) > 0:
                    # 30天涨幅超过20%
                    if data.lines.close[-30] * 1.2 < data.lines.close[0]:
                        # self.log("%s ,-30 close %2.f,close %2.f" % (
                        #     data._name, data.lines.close[-30], data.lines.close[0]))

                        high = max(data.lines.high.get(size=10))
                        low = min(data.lines.low.get(size=10))

                        xt_high = self.sma[0] * 1.03
                        xt_low = self.sma[0] * 0.97

                        if high < xt_high and low > xt_low:
                            self.log('买入 %s , %.2f' % (data._name, data.close[0]))
                            self.sendmsg(data=data)
                            self.buy(data=data)
            else:
                if pos.price * 1.1 < data.lines.close[0]:
                    self.log('卖出 %s , %.2f' % (data._name, data.close[0]))
                    self.close(data=data)

import backtrader as bt
import datetime
import redis


# https://mp.weixin.qq.com/s/g8TyAWZABtOc8Ir6vWe18Q
# 大小盘轮动策略
class StrategyBigSmallRotate(bt.Strategy):
    params = dict(period=20)

    def log(self, txt, dt=None):
        """Logging function for this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):

        self.sma = dict()
        self.stock_data = dict()
        for data in self.datas:
            self.sma[data._name] = bt.indicators.MovingAverageSimple(
                data, period=self.params.period)
            self.stock_data[data._name] = data

        self.big_ratio = (self.stock_data['510050'].close / self.sma['510050']) - 1
        self.small_ratio = (self.stock_data['159949'].close / self.sma['159949']) - 1

        self.big_signal = bt.And(self.big_ratio > 0, self.big_ratio > self.small_ratio)
        self.small_signal = bt.And(self.small_ratio > 0, self.small_ratio > self.big_ratio)
        self.close_signal = bt.And(self.big_ratio < 0, self.small_ratio < 0)

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
        pos = dict()
        for data in self.datas:
            pos[data._name] = self.getposition(data)
            if self.close_signal and pos[data._name].size:
                self.close(data=data)

        # self.log("510050 的价格: %.2f, 510050 的均价: %.2f, 159949 的价格: %.2f, 159949 的均价: %.2f" % (
        #     self.stock_data['510050'].close[0], self.sma['510050'][0], self.stock_data['159949'].close[0],
        #     self.sma['159949'][0]))

        for data in self.datas:
            if data._name == "510050" and self.big_signal:
                if pos['159949'].size:
                    self.close(data=self.stock_data['159949'])
                if not pos['510050'].size:
                    self.buy(data=data)
            if data._name == "159949" and self.small_signal:
                if pos['510050'].size:
                    self.close(data=self.stock_data['510050'])
                if not pos['159949'].size:
                    self.buy(data=data)

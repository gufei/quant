import backtrader as bt
from datetime import datetime, timedelta


class MomentumStrategy(bt.Strategy):
    params = dict(period=21)

    def __init__(self):
        self.inds = dict()
        for d in self.datas:
            self.inds[d] = dict()
            self.inds[d]['roc'] = bt.indicators.RateOfChange100(d.close, period=self.p.period)  # 计算涨跌幅
            self.inds[d]['order'] = None  # 保存订单
            self.inds[d]['buyprice'] = None
            self.inds[d]['buycomm'] = None

    def next(self):
        # 检查是否是月末
        # for d in self.datas:
        dt = self.datas[0].datetime.date(0)
        if dt.month != (dt + timedelta(days=3)).month:  # 如果3天后是下个月，则今天是月末
            self.rebalance_portfolio()

    def rebalance_portfolio(self):
        # 每个月的最后一个交易日，选择过去21个交易日涨幅最大的ETF
        roc_values = {d: self.inds[d]['roc'][0] for d in self.datas}
        max_roc_d = max(roc_values, key=roc_values.get)  # 取涨幅最大的ETF

        # 如果当前持有的ETF不是涨幅最大的，那么卖出当前持有的ETF，买入涨幅最大的ETF
        for d in self.datas:
            if self.getposition(d).size:  # 如果持有ETF
                if d != max_roc_d:  # 如果不是涨幅最大的ETF，卖出
                    self.inds[d]['order'] = self.close(data=d)
        for d in self.datas:
            if not self.getposition(d).size and d == max_roc_d:  # 如果是涨幅最大的ETF,并且没有持仓，买入
                self.inds[d]['order'] = self.buy(data=d)

    def log(self, txt, dt=None):
        """Logging function for this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

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

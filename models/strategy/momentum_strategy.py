import backtrader as bt
from datetime import timedelta


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

        dt = self.datas[0].datetime.date(0)
        # 检查是否是月末
        if dt.month != (dt + timedelta(days=3)).month:  # 如果3天后是下个月，则今天是月末,这里只考虑周末的因素，不考虑长假的因素
            roc_values = {d: self.inds[d]['roc'][0] for d in self.datas}
            self.max_roc_d = max(roc_values, key=roc_values.get)  # 取涨幅最大的ETF
            self.rebalance_portfolio_sell()

        # 检查是否是月初
        if dt.month != self.datas[0].datetime.date(-1).month:
            self.rebalance_portfolio_buy()

    def rebalance_portfolio_sell(self):
        # 如果当前持有的ETF不是涨幅最大的，那么卖出当前持有的ETF，买入涨幅最大的ETF
        for d in self.datas:
            if self.getposition(d).size:  # 如果持有ETF
                if d != self.max_roc_d:  # 如果不是涨幅最大的ETF，卖出
                    self.inds[d]['order'] = self.close(data=d)
                    self.log(
                        '发送卖出指令，卖出 %s, open price %.2f, close price %.2f, 当前持仓数量 %i, 当前持仓成本 %.2f' % (
                            d._name, d.open[0], d.close[0], self.broker.getposition(d).size,
                            self.broker.getposition(d).price))

    def rebalance_portfolio_buy(self):
        # 每个月的最后一个交易日，选择过去21个交易日涨幅最大的ETF
        for d in self.datas:
            if not self.getposition(d).size and d == self.max_roc_d:  # 如果是涨幅最大的ETF,并且没有持仓，买入
                self.inds[d]['order'] = self.buy(data=d)
                self.log('发送购买指令，买入 %s, open price %.2f, close price %.2f' % (d._name, d.open[0], d.close[0]))

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
                    '买入 %s 执行成功, 单价: %.2f, 数量: %i, 总金额: %.2f, 手续费 %.2f' %
                    (order.data._name, order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('卖出 %s 执行成功, 单价: %.2f, 数量: %i,总金额: %.2f, 手续费 %.2f' %
                         (order.data._name, order.executed.price,
                          order.executed.size,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        else:
            self.log('订单作废 %s, %s, isbuy=%i, size %i, open price %.2f, close price %.2f' %
                     (order.data._name, order.getstatusname(), order.isbuy(), order.created.size, order.data.open[0],
                      order.data.close[0]))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('毛收益 %0.2f, 扣佣后收益 % 0.2f, 佣金 %.2f, 市值 %.2f, 现金 %.2f' %
                 (trade.pnl, trade.pnlcomm, trade.commission, self.broker.getvalue(), self.broker.getcash()))

import backtrader as bt


# 最低5元，卖出收千一的印花税
class MyCommission(bt.CommInfoBase):
    def _getcommission(self, size, price, pseudoexec):
        if self.p.commission == 0:
            return 0
        # basic commission
        comm = max(5, abs(size * price * self.p.commission))
        # stamp tax, only sell order
        if size < 0:
            comm -= size * price * 0.001
        return comm

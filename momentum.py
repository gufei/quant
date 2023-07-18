import os
import datetime

import backtrader as bt
import models.commissions.mycommission as my_commission

import models.strategy.momentum_strategy as momentum_strategy

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

    index_stock_cons_csindex_df = ['518880', '513100', '159915', '510300']

    for stock in index_stock_cons_csindex_df:
        file = "./data/day/" + stock + ".csv"

        if not os.path.isfile(file):
            print(file + " 文件不存在")
            continue

        data = bt.feeds.GenericCSVData(
            dataname=file,
            # fromdate=datetime.datetime(2022, 1, 1),
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

    cerebro.addstrategy(momentum_strategy.MomentumStrategy)

    # 添加分析指标
    # 返回年初至年末的年度收益率
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn')
    # 计算最大回撤相关指标
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown')
    # 计算年化收益：日度收益
    cerebro.addanalyzer(bt.analyzers.Returns, _name='_Returns', tann=252)
    # 计算年化夏普比率：日度收益
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio', timeframe=bt.TimeFrame.Days, annualize=True,
                        riskfreerate=0)
    # 计算夏普比率：年化
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='_SharpeRatio_A')
    # 返回收益率时序
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')

    print('回测开始，资产价值: %.2f' % cerebro.broker.getvalue())

    result = cerebro.run()

    print('回测完成，资产价值: %.2f' % cerebro.broker.getvalue())

    # 提取结果
    print("--------------- 年初至年末的年度收益率 -----------------")
    print(result[0].analyzers._AnnualReturn.get_analysis())
    print("--------------- 最大回撤相关 -----------------")
    print(result[0].analyzers._DrawDown.get_analysis())
    print("--------------- 计算年化收益：日度收益 -----------------")
    print(result[0].analyzers._Returns.get_analysis())
    print("--------------- 年化夏普比率：日度收益 -----------------")
    print(result[0].analyzers._SharpeRatio.get_analysis())
    print("--------------- 夏普比率：年化 -----------------")
    print(result[0].analyzers._SharpeRatio_A.get_analysis())
    # print("--------------- 收益率时序 -----------------")
    # print(result[0].analyzers._TimeReturn.get_analysis())
    #
    cerebro.plot()

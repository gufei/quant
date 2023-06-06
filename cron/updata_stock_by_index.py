import akshare as ak

import pandas as pd

start_data = "20230101"
symbol = "000906"

# 获取中证 800 成份股
index_stock_cons_csindex_df = ak.index_stock_cons_csindex(symbol=symbol)

for _, stock in index_stock_cons_csindex_df.iterrows():
    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock['成分券代码'], period="daily", start_date="20230101",
                                            adjust="qfq")

    stock_zh_a_hist_df.columns = [
        'date',  # 日期
        'open',  # 开盘
        'close',  # 收盘
        'high',  # 最高
        'low',  # 最低
        'volume',  # 成交量
        'turnover',  # 成交额
        'amplitude',  # 振幅
        'change',  # 涨跌幅
        'change_amount',  # 涨跌额
        'turnover_rate',  # 换手率
    ]
    # stock_zh_a_hist_df.index = pd.to_datetime(stock_zh_a_hist_df['date'])

    # print(stock_zh_a_hist_df)

    stock_zh_a_hist_df.to_csv("./data/day/" + stock['成分券代码'] + ".csv", index=None)

    print(stock['成分券代码'], stock['成分券名称'], "done")

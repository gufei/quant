import pandas as pd
import qstock as qs

start_data = "20230101"
symbol = "zz800"

cf = qs.index_member(symbol)

df = qs.get_data(cf['股票代码'], start=start_data)
order = ['open', 'close', 'high', 'low', 'volume', 'turnover', 'turnover_rate', 'name', 'code']
df = df[order]

g_df = df.groupby('code')

for name, group in g_df:
    group.to_csv("./data/day/" + name + ".csv")

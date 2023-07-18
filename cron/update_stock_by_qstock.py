import pandas as pd
import qstock as qs

start_data = "20230101"
symbol = "zz800"

# cf = qs.index_member(symbol)
#
# stock_arr = cf['股票代码'].tolist()
# stock_arr.append('510050')
# stock_arr.append('159949')

stock_arr = list()

# stock_arr.append('159967')
# stock_arr.append('512890')
#
# stock_arr.append('511220')  # 城投债
# stock_arr.append('512010')  # 医药
stock_arr.append('518880')  # 黄金
# stock_arr.append('163415')  # 兴全商业
# stock_arr.append('159928')  # 消费
# stock_arr.append('161903')  # 万家行业优选
stock_arr.append('513100')  # 纳指

# stock_arr.append('600150')  # 中国船舶
# stock_arr.append('000001')  # 平安银行
# stock_arr.append('002142')  # 宁波银行

stock_arr.append('159915')  # 创业板
stock_arr.append('510300')  # 沪深300

df = qs.get_data(stock_arr, fqt=1)
order = ['open', 'close', 'high', 'low', 'volume', 'turnover', 'turnover_rate', 'name', 'code']
df = df[order]

g_df = df.groupby('code')

for name, group in g_df:
    group.to_csv("./data/day/" + name + ".csv")

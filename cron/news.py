import sys
import os
import time

sys.path.append(os.path.dirname(sys.path[0]))

import datetime
import qstock as qs
import utils.notify as notify
import re

# 10分钟内新闻
release_datetime = (datetime.datetime.now() + datetime.timedelta(minutes=-10))

df = qs.news_data()

for _, new in df[(df.发布日期 == release_datetime.date()) & (df.发布时间 > release_datetime.time())].iterrows():
    msg = new['内容']
    pattern = r"财联社\d+月\d+日电，"
    msg = re.sub(pattern, "", msg)
    notify.send_msg_by_redis("news", msg)
    time.sleep(5)

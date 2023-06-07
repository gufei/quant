import sys
import os

sys.path.append(os.path.dirname(sys.path[0]))

import datetime
import qstock as qs
import utils.notify as notify

# 10分钟内新闻
release_time = (datetime.datetime.now() + datetime.timedelta(minutes=-10)).time()

df = qs.news_data()

for _, new in df[df.发布时间 > release_time].iterrows():
    msg = new['内容']
    notify.send_msg_by_redis(msg)

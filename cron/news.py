import sys
import os
import time

sys.path.append(os.path.dirname(sys.path[0]))

import datetime
import qstock as qs
import utils.notify as notify
import re
import feedparser
import pandas as pd
import pytz

beijing_tz = pytz.timezone('Asia/Shanghai')


def rss_news(url, datetime_format="%Y-%m-%d %H:%M:%S", is_utc=False, start=None, end=None):
    # RSS订阅源的URL
    # url = "https://www.chaincatcher.com/rss/clist"
    # 解析RSS订阅源
    feed = feedparser.parse(url)
    # 创建一个空的DataFrame来存储数据
    data = pd.DataFrame(columns=["标题", "内容", "发布时间", "发布日期", "摘要", "链接"])

    if is_utc and start is not None:
        start = beijing_tz.localize(start)
    if is_utc and end is not None:
        end = beijing_tz.localize(end)
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        published = entry.published
        summary = entry.summary

        published_datetime = datetime.datetime.strptime(published, datetime_format)

        if is_utc:
            published_datetime = published_datetime.replace(tzinfo=pytz.utc).astimezone(beijing_tz)

        if start is not None and published_datetime < start:
            break
        if end is not None and published_datetime > end:
            break
        entry_Data = {"标题": [title], "内容": ["【" + title + "】" + summary],
                      "发布时间": [published_datetime.strftime("%H:%M:%S")],
                      "发布日期": [published_datetime.strftime("%Y-%m-%d")],
                      "摘要": [summary], "链接": [link]}
        entry_df = pd.DataFrame(entry_Data)

        data = pd.concat([data, entry_df], ignore_index=True)

    return data


# 10分钟内新闻
release_datetime = (datetime.datetime.now() + datetime.timedelta(minutes=-10))

cls_df = qs.news_data()

cls_df = cls_df[(cls_df.发布日期 == release_datetime.date()) & (cls_df.发布时间 > release_datetime.time())]

chaincatcher_df = rss_news("https://www.chaincatcher.com/rss/clist", datetime_format="%Y-%m-%d %H:%M:%S",
                           start=release_datetime)
panewslab_df = rss_news("https://rsshub.app/panewslab/news", datetime_format="%a, %d %b %Y %H:%M:%S %Z", is_utc=True,
                        start=release_datetime)
odaily_df = rss_news("https://rsshub.app/odaily/newsflash", datetime_format="%a, %d %b %Y %H:%M:%S %Z", is_utc=True,
                     start=release_datetime)

df = pd.concat([cls_df, chaincatcher_df, panewslab_df, odaily_df], ignore_index=True)

for _, new in df.iterrows():
    msg = new['内容']
    pattern = r"财联社(\d+月\d+日)电，"
    replacement = r"\1，"
    msg = re.sub(pattern, replacement, msg)
    notify.send_msg_by_redis("news", msg)
    time.sleep(5)

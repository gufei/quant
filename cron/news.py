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
import multitasking
import signal
from tqdm import tqdm
import requests

signal.signal(signal.SIGINT, multitasking.killall)

beijing_tz = pytz.timezone('Asia/Shanghai')

new_columns = ["标题", "内容", "发布时间", "发布日期", "摘要", "链接"]

# 10分钟内新闻
release_datetime = (datetime.datetime.now() + datetime.timedelta(minutes=-10))


def odaily_news(start=None, end=None):
    url = "https://www.odaily.news/api/pp/api/info-flow/newsflash_columns/newsflashes"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-SG,zh;q=0.9,en-SG;q=0.8,en;q=0.7,zh-CN;q=0.6",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json;charset=utf-8",
        "Pragma": "no-cache",
        "Referer": "https://www.odaily.news/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    }
    data = requests.get(url, headers=headers).json()
    df = pd.DataFrame(data["data"]["items"])
    df = df[["title", "description", "published_at", "news_url"]]
    df["published_at"] = pd.to_datetime(df["published_at"])
    df.columns = ["标题", "摘要", "发布时间", "链接"]
    df.sort_values(["发布时间"], inplace=True)
    df.reset_index(inplace=True, drop=True)

    if start is not None:
        df = df[df.发布时间 >= start]
    if end is not None:
        df = df[df.发布时间 <= end]
    df["发布日期"] = df["发布时间"].dt.date
    df["发布时间"] = df["发布时间"].dt.time
    df["内容"] = "【" + df["标题"] + "】" + df["摘要"]

    return df.reindex(columns=new_columns)


odaily_df = odaily_news(start=release_datetime)

cls_df = qs.news_data()

cls_df = cls_df[(cls_df.发布日期 == release_datetime.date()) & (cls_df.发布时间 > release_datetime.time())]

data_list = [cls_df, odaily_df]


@multitasking.task
def rss_news(url, datetime_format="%Y-%m-%d %H:%M:%S", is_utc=False, start=None, end=None):
    # 解析RSS订阅源
    feed = feedparser.parse(url)
    # 创建一个空的DataFrame来存储数据
    data = pd.DataFrame(columns=new_columns)

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
        else:
            published_datetime = published_datetime.replace(tzinfo=None)

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
    data_list.append(data)
    pbar.update()


pbar = tqdm(total=2)
rss_news("https://www.chaincatcher.com/rss/clist", datetime_format="%Y-%m-%d %H:%M:%S",
         start=release_datetime)
rss_news("https://rss.panewslab.com/zh/tvsq/rss", datetime_format="%a, %d %b %Y %H:%M:%S %z",
         start=release_datetime)

multitasking.wait_for_tasks()

new_df = pd.concat(data_list, ignore_index=True)

for _, new in new_df.iterrows():
    msg = new['内容']

    # pattern = r"财联社(\d+月\d+日)电，"
    # replacement = r"\1，"
    # msg = re.sub(pattern, replacement, msg)
    #
    # pattern = r"PANews (\d+月\d+日)消息，"
    # replacement = r"\1消息，"
    # msg = re.sub(pattern, replacement, msg)
    #
    # pattern = r"Odaily星球日报讯 "
    # msg = re.sub(pattern, "", msg)
    #
    # pattern = r"ChainCatcher 消息，"
    # msg = re.sub(pattern, "", msg)

    notify.send_msg_by_redis("news", msg)
    time.sleep(5)

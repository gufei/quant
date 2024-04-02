import sys
import os
import time

from bs4 import BeautifulSoup

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
import json

signal.signal(signal.SIGINT, multitasking.killall)

beijing_tz = pytz.timezone('Asia/Shanghai')

new_columns = ["标题", "内容", "发布时间", "发布日期", "摘要", "链接", "来源"]

# 10分钟内新闻
release_datetime = (datetime.datetime.now() + datetime.timedelta(minutes=-10))


def sendWxHook(new):
    url = "http://172.23.24.97:30001/SendTextMsg"

    try:
        soup = BeautifulSoup(new['摘要'], 'html5lib')
        text = soup.get_text()
    except:
        return

    payload = json.dumps({
        "wxid": "34962679447@chatroom",
        "msg": text
    })

    headers = {
        'Content-Type': 'application/json'
    }

    requests.request("POST", url, headers=headers, data=payload)


def sendFs(new):
    url = "https://open.larksuite.com/open-apis/bot/v2/hook/2c3ea65b-9c07-46b6-b77e-6b6bfc506952"

    try:
        soup = BeautifulSoup(new['摘要'], 'html5lib')
        text = soup.get_text()
    except:
        return

    payload = json.dumps({
        "msg_type": "interactive",
        "card": {
            "elements": [
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": False,
                            "text": {
                                "tag": "lark_md",
                                "content": "**发布时间：**" + new['发布日期'] + " " + new['发布时间']
                            }
                        }
                    ]
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "content": text,
                        "tag": "lark_md"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "content": "阅读原文",
                                "tag": "lark_md"
                            },
                            "url": new['链接'],
                            "type": "primary",
                            "value": {}
                        }
                    ],
                    "tag": "action"
                }
            ],
            "header": {
                "title": {
                    "content": new['标题'],
                    "tag": "plain_text"
                },
                "template": "green"
            }
        }
    })

    headers = {
        'Content-Type': 'application/json'
    }

    requests.request("POST", url, headers=headers, data=payload)


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
    df["发布日期"] = df["发布时间"].dt.strftime("%Y-%m-%d")
    df["发布时间"] = df["发布时间"].dt.strftime("%H:%M:%S")
    df["内容"] = "【" + df["标题"] + "】" + df["摘要"]
    df["来源"] = "odaily"

    return df.reindex(columns=new_columns)


def binance_news(start=None, end=None):
    url = "https://www.binance.com/bapi/composite/v1/friendly/pgc/news/list"
    headers = {
        "Content-Type": "application/json",
        "lang": "zh-CN",
        "Referer": "https://www.binance.com/zh-CN/feed/news",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    }
    payload = json.dumps({
        "pageIndex": 1,
        "pageSize": 50
    })
    data = requests.post(url, headers=headers, data=payload).json()

    df = pd.DataFrame(data["data"]["vos"])
    df = df[["title", "subTitle", "date", "webLink"]]
    df["date"] = pd.to_datetime(df["date"], unit='s').dt.tz_localize('UTC').dt.tz_convert("Asia/Shanghai")
    df.columns = ["标题", "摘要", "发布时间", "链接"]
    df.sort_values(["发布时间"], ascending=False, inplace=True)
    df.reset_index(inplace=True, drop=True)

    if start is not None:
        start_beijing = start.astimezone(beijing_tz)
        df = df[df.发布时间 >= start_beijing]
    if end is not None:
        end_beijing = end.astimezone(beijing_tz)
        df = df[df.发布时间 <= end_beijing]
    df["发布日期"] = df["发布时间"].dt.strftime("%Y-%m-%d")
    df["发布时间"] = df["发布时间"].dt.strftime("%H:%M:%S")
    df["内容"] = "【" + df["标题"] + "】" + df["摘要"]
    df["来源"] = "binance"

    return df.reindex(columns=new_columns)


binance_df = binance_news(start=release_datetime)

odaily_df = odaily_news(start=release_datetime)

cls_df = qs.news_data()

cls_df = cls_df[(cls_df.发布日期 == release_datetime.date()) & (cls_df.发布时间 > release_datetime.time())]

data_list = [cls_df, odaily_df, binance_df]


@multitasking.task
def rss_news(url, datetime_format="%Y-%m-%d %H:%M:%S", is_utc=False, start=None, end=None, source=""):
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
                      "摘要": [summary], "链接": [link], "来源": source}
        entry_df = pd.DataFrame(entry_Data)

        data = pd.concat([data, entry_df], ignore_index=True)
    data_list.append(data)
    pbar.update()


pbar = tqdm(total=2)
rss_news("https://www.chaincatcher.com/rss/clist", datetime_format="%Y-%m-%d %H:%M:%S",
         start=release_datetime, source="chaincatcher")
rss_news("https://rss.panewslab.com/zh/tvsq/rss", datetime_format="%a, %d %b %Y %H:%M:%S %z",
         start=release_datetime, source="panewslab")

multitasking.wait_for_tasks()

new_df = pd.concat(data_list, ignore_index=True)

for _, new in new_df.iterrows():
    # msg = new['内容']
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

    # notify.send_msg_by_redis("news", msg)

    sendWxHook(new)

    if new["来源"] in ["chaincatcher", "panewslab", "odaily", "binance"]:
        sendFs(new)

    time.sleep(1)

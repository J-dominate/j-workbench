#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性引导脚本：用已抓取到的真实条目组装 news.json（不联网）。"""
import json, datetime, time

now = int(time.time() * 1000)

def ts_from(s):
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return int(datetime.datetime.strptime(s, fmt).timestamp() * 1000)
        except Exception:
            pass
    return now

raw = [
    # ---- 36氪 (财经/金融) ----
    ("36氪", "财经", "硬氪首发 | 深圳具身基础设施公司获近亿元融资，拿下60%估值百亿头部机器人公司客户", "https://36kr.com/p/3954612909227138?f=rss", "2026-08-25 17:58:11 +0800"),
    ("36氪", "财经", "36氪首发｜东方非遗香氛品牌「呈白」完成数千万元Pre-A轮融资，上影新视野独家投资", "https://36kr.com/p/3947925280832901?f=rss", "2026-08-25 10:00:00 +0800"),
    ("36氪", "财经", "8点1氪丨“敌敌畏消杀餐厅”事件已成立联合调查组；小鹏机器人首轮融资超9亿美元；东方甄选薪酬少发4个亿", "https://36kr.com/p/3954181545753728?f=rss", "2026-08-25 08:01:38 +0800"),
    ("36氪", "财经", "对话昆仑行创始人任庚：车企做具身，未来入场是“战略必然”，现在切入是“战术投机”", "https://36kr.com/p/3953725993991560?f=rss", "2026-08-25 00:18:16 +0800"),
    ("36氪", "财经", "字节探索自动驾驶，Seed世界模型团队负责｜36氪独家", "https://36kr.com/p/3953699726343556?f=rss", "2026-08-24 23:51:37 +0800"),
    ("36氪", "财经", "在轨3年、全栈自研，宇航级热控方案供应商「锐莱热控」获A+轮数千万融资｜36氪首发", "https://36kr.com/p/3953370022034820?f=rss", "2026-08-24 18:33:16 +0800"),
    ("36氪", "财经", "这场AI大赛上，年轻人把「人味」拉满了", "https://36kr.com/p/3953254092062085?f=rss", "2026-08-24 16:19:21 +0800"),
    # ---- 中国政府网 (政策) ----
    ("中国政府网", "政策", "中共中央办公厅 国务院办公厅印发《党政领导干部生态环境损害责任追究办法》", "https://www.gov.cn/yaowen/liebiao/202608/content_7079095.htm", ""),
    ("中国政府网", "政策", "国务院关于修改《住房公积金管理条例》的决定", "https://www.gov.cn/zhengce/content/202608/content_7078477.htm", ""),
    ("中国政府网", "政策", "国务院关于《特殊教育发展提升“十五五”行动计划》的批复", "https://www.gov.cn/zhengce/content/202608/content_7078320.htm", ""),
    ("中国政府网", "政策", "国家发展改革委、国家能源局印发《石油天然气发展“十五五”规划》", "https://www.gov.cn/lianbo/202608/content_7078379.htm", ""),
    ("中国政府网", "政策", "李强主持召开国务院常务会议 听取新一代通信网建设情况汇报等", "https://www.gov.cn/yaowen/liebiao/202608/content_7078803.htm", ""),
]

items = []
for src, cat, title, link, pub in raw:
    items.append({
        "title": title,
        "link": link,
        "source": src,
        "cat": cat,
        "desc": "",
        "pubDate": pub,
        "ts": ts_from(pub),
    })

payload = {
    "generatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "count": len(items),
    "sources": {"36氪": 7, "中国政府网": 5},
    "items": items,
}
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
print("wrote", len(items), "items -> news.json")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 fetched.json（由 WebFetch 抓取的多源原始数据）合并、去重、整理成 news.json。
fetched.json 结构: [ {source, cat, title, link, pubDate, desc?}, ... ]
输出 news.json 结构: { generated, count, sources, items:[...] }
"""
import json
import re
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
FETCHED = os.path.join(HERE, "fetched.json")
OUT = os.path.join(HERE, "news.json")

CAT_DEFAULT = {
    "36氪": "财经",
    "东方财富": "金融",
    "中国政府网": "政策",
    "新浪财经": "财经",
    "财新": "财经",
    "第一财经": "财经",
}


def clean(s):
    if not s:
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


def main():
    if not os.path.exists(FETCHED):
        print("fetched.json 不存在，退出")
        return
    raw = json.load(open(FETCHED, encoding="utf-8"))
    seen = set()
    items = []
    for it in raw:
        source = clean(it.get("source")) or "未知"
        title = clean(it.get("title"))
        link = clean(it.get("link"))
        if not title or not link:
            continue
        cat = clean(it.get("cat")) or CAT_DEFAULT.get(source, "资讯")
        key = (source + "|" + title).replace(" ", "").lower()[:80]
        if key in seen:
            continue
        seen.add(key)
        items.append({
            "source": source,
            "cat": cat,
            "title": title,
            "link": link,
            "desc": clean(it.get("desc"))[:160],
            "ts": int(datetime.now(timezone.utc).timestamp() * 1000),
        })
    items.sort(key=lambda x: x["title"])
    counts = {}
    for i in items:
        counts[i["source"]] = counts.get(i["source"], 0) + 1
    out = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(items),
        "sources": counts,
        "items": items[:40],
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"news.json 已生成：{out['count']} 条，来源 {counts}")


if __name__ == "__main__":
    main()

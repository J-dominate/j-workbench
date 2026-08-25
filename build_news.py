#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J 工作台 · 信息日报 聚合脚本 (服务器端运行)
- 在 GitHub Actions runner 上抓取多个国内财经/政策/金融 RSS 源
- 去重合并后生成 news.json，由 GitHub Pages 托管，浏览器直接同源读取
- 不依赖任何前端 CORS 代理，国内访问稳定
"""
import urllib.request
import urllib.error
import json
import re
import ssl
import datetime
import sys

# 关闭证书校验（个别政府站点证书老旧），仅用于 RSS 抓取
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE

# 数据源：name=显示名, cat=分类, urls=候选地址（按顺序尝试，命中即停）
SOURCES = [
    {"name": "36氪",       "cat": "财经", "urls": ["https://36kr.com/feed"]},
    {"name": "华尔街见闻", "cat": "金融", "urls": ["https://rsshub.app/wallstreetcn/news",
                                                "https://rsshub.rssforever.com/wallstreetcn/news"]},
    {"name": "财新网",     "cat": "财经", "urls": ["https://rsshub.app/caixin/latest",
                                                "https://rsshub.rssforever.com/caixin/latest"]},
    {"name": "第一财经",   "cat": "财经", "urls": ["https://rsshub.app/yicai/index",
                                                "https://rsshub.rssforever.com/yicai/index"]},
    {"name": "证券时报",   "cat": "金融", "urls": ["https://rsshub.app/stcn/news",
                                                "https://rsshub.rssforever.com/stcn/news"]},
    {"name": "新华财经",   "cat": "财经", "urls": ["http://www.news.cn/fortune/rss.xml"]},
    {"name": "中国政府网", "cat": "政策", "urls": ["http://www.gov.cn/zhengce/zuixin/zhengcefabu/zhengcefabu/rss.xml"]},
    {"name": "凤凰财经",   "cat": "财经", "urls": ["https://ishare.ifeng.com/rss/"]},
    {"name": "新浪财经",   "cat": "财经", "urls": ["https://finance.sina.com.cn/roll/rss.php?cid=1"]},
    {"name": "央视新闻",   "cat": "政治", "urls": ["https://rsshub.app/cctv/vnews",
                                                "https://rsshub.rssforever.com/cctv/vnews"]},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JWorkbenchNewsBot/1.0)",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def fetch_text(url, timeout=18):
    last_err = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as resp:
                raw = resp.read()
            # 尝试 utf-8，失败再 gbk
            for enc in ("utf-8", "gbk", "gb18030"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", "ignore")
        except Exception as e:  # noqa
            last_err = e
            continue
    sys.stderr.write(f"[warn] fetch failed: {url} -> {last_err}\n")
    return ""


def clean(txt):
    if not txt:
        return ""
    txt = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", txt, flags=re.S)
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = (
        txt.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
    )
    return re.sub(r"\s+", " ", txt).strip()


def parse_items(xml, source, cat):
    if not xml:
        return []
    # 兼容 RSS(<item>) 与 Atom(<entry>)
    blocks = re.findall(r"<item[ >].*?</item>", xml, re.S | re.I)
    if not blocks:
        blocks = re.findall(r"<entry[ >].*?</entry>", xml, re.S | re.I)
    out = []
    for b in blocks[:8]:
        t = re.search(r"<title[^>]*>(.*?)</title>", b, re.S | re.I)
        # link: Atom 的 <link href="..."/> 优先；否则 RSS 的 <link>text</link>
        lk = re.search(r"<link[^>]*href=\"([^\"]+)\"", b, re.S | re.I)
        if not lk:
            lk = re.search(r"<link[^>]*>(.*?)</link>", b, re.S | re.I)
        pd = re.search(r"<pubDate[^>]*>(.*?)</pubDate>", b, re.S | re.I) or re.search(
            r"<updated[^>]*>(.*?)</updated>", b, re.S | re.I
        )
        dc = re.search(r"<description[^>]*>(.*?)</description>", b, re.S | re.I) or re.search(
            r"<summary[^>]*>(.*?)</summary>", b, re.S | re.I
        )
        title = clean(t.group(1)) if t else ""
        link = clean(lk.group(1)) if lk else ""
        pub = clean(pd.group(1)) if pd else ""
        desc = clean(dc.group(1))[:200] if dc else ""
        if not title or not link:
            continue
        ts = 0
        if pub:
            try:
                ts = int(datetime.datetime.fromisoformat(pub.replace("Z", "+00:00")).timestamp() * 1000)
            except Exception:  # noqa
                try:
                    ts = int(datetime.datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %z").timestamp() * 1000)
                except Exception:  # noqa
                    ts = 0
        out.append({
            "title": title,
            "link": link,
            "source": source,
            "cat": cat,
            "desc": desc,
            "pubDate": pub,
            "ts": ts,
        })
    return out


def main():
    all_items = []
    per_source = {}
    for s in SOURCES:
        items = []
        for url in s["urls"]:
            items = parse_items(fetch_text(url), s["name"], s["cat"])
            if items:
                break
        per_source[s["name"]] = len(items)
        all_items.extend(items)

    # 去重（来源+标题）
    seen = set()
    dedup = []
    for it in all_items:
        k = (it["source"] + "|" + it["title"]).replace(" ", "")
        if k in seen:
            continue
        seen.add(k)
        dedup.append(it)

    # 按时间倒序（无时间的排末尾）
    dedup.sort(key=lambda x: x["ts"] or 0, reverse=True)
    top = dedup[:40]

    payload = {
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(top),
        "sources": per_source,
        "items": top,
    }
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    ok = {k: v for k, v in per_source.items() if v}
    sys.stderr.write(f"[done] total={len(all_items)} dedup={len(dedup)} -> top={len(top)}\n")
    sys.stderr.write(f"[ok sources] {ok}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa
        import traceback
        traceback.print_exc()
        sys.stderr.write("CRASH: " + repr(e) + "\n")
        sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
央视栏目 RSS 生成器（多栏目集中版）
====================================
读取 config/columns.json 中的栏目配置，逐个调用央视官方接口
api.cntv.cn，生成标准 RSS 2.0 文件到 feeds/<栏目id>.xml，
同时生成 feeds/index.html 订阅索引页。

用法：
    python3 scripts/cctv_rss.py

添加新栏目：编辑 config/columns.json，加一行即可。
"""
import json
import os
import sys
import html
import urllib.request
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "columns.json")
FEEDS_DIR = os.path.join(BASE_DIR, "feeds")
CST = timezone(timedelta(hours=8))

API_TEMPLATE = (
    "https://api.cntv.cn/NewVideo/getVideoListByColumn"
    "?id={topc}&n=20&sort=desc&p=1&mode=0&serviceId=tvcctv"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://tv.cctv.com/",
}


def fetch_column(topc):
    url = API_TEMPLATE.format(topc=topc)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def rfc822(text):
    try:
        dt = datetime.strptime(text.strip(), "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=CST)
        return format_datetime(dt)
    except Exception:
        return None


def build_rss(col, data):
    items = data.get("data", {}).get("list", [])
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "<channel>",
        f"<title>{html.escape(col['name'])} - 视频更新</title>",
        f"<link>{html.escape(col.get('url', ''))}</link>",
        f"<description>{html.escape(col.get('desc', col['name'] + ' 栏目视频更新'))}</description>",
        "<language>zh-cn</language>",
        f"<lastBuildDate>{format_datetime(datetime.now(CST))}</lastBuildDate>",
    ]
    for it in items:
        title = (it.get("title") or "").strip()
        link = (it.get("url") or "").strip()
        guid = it.get("guid") or link
        image = (it.get("image") or "").strip()
        brief = (it.get("brief") or "").strip().replace("\r\n", "\n").replace("\n", "<br/>")
        pub = rfc822(it.get("time", ""))
        out.append("<item>")
        out.append(f"<title>{html.escape(title)}</title>")
        out.append(f"<link>{html.escape(link)}</link>")
        out.append(f'<guid isPermaLink="true">{html.escape(guid)}</guid>')
        if pub:
            out.append(f"<pubDate>{pub}</pubDate>")
        desc = (f'<p><img src="{html.escape(image, quote=True)}" width="320"/></p><p>{brief}</p>'
                if image else f"<p>{brief}</p>")
        out.append(f"<description>{html.escape(desc)}</description>")
        out.append("</item>")
    out.append("</channel></rss>")
    return "\n".join(out)


def build_index(columns, results):
    rows = []
    for col, ok in results:
        status = "✅ 正常" if ok else "❌ 失败"
        feed_url = f"feeds/{col['id']}.xml"
        rows.append(
            f"<tr><td>{html.escape(col['name'])}</td>"
            f"<td><code>{col['id']}</code></td>"
            f"<td>{status}</td>"
            f'<td><a href="{feed_url}">{feed_url}</a></td></tr>'
        )
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S %z")
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>央视栏目 RSS 订阅索引</title>
<style>body{{font-family:-apple-system,sans-serif;max-width:720px;margin:40px auto;padding:0 16px;color:#222}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#f5f5f5}}code{{background:#f0f0f0;padding:2px 6px;border-radius:4px}}</style>
</head><body>
<h1>央视栏目 RSS 订阅索引</h1>
<p>最后更新：{now}（由 GitHub Actions 定时生成）</p>
<table><tr><th>栏目</th><th>ID</th><th>状态</th><th>订阅地址</th></tr>
{''.join(rows)}
</table>
<p>把订阅地址粘贴到 RSS 阅读器（如 Feedbro）即可。</p>
</body></html>"""


def main():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        columns = json.load(f)

    os.makedirs(FEEDS_DIR, exist_ok=True)
    results = []

    for col in columns:
        print(f"处理栏目：{col['name']} ({col['id']}) ...", end=" ")
        try:
            data = fetch_column(col["topc"])
            xml = build_rss(col, data)
            out_path = os.path.join(FEEDS_DIR, f"{col['id']}.xml")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(xml)
            count = len(data.get("data", {}).get("list", []))
            print(f"OK，{count} 条")
            results.append((col, True))
        except Exception as e:
            print(f"失败：{e}")
            results.append((col, False))

    index_html = build_index(columns, results)
    with open(os.path.join(FEEDS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"索引页已生成：feeds/index.html")

    # 任何一个栏目失败都返回非零，方便 Actions 告警
    if not all(ok for _, ok in results):
        sys.exit(1)


if __name__ == "__main__":
    main()

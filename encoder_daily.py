import os
import re
import html
import smtplib
import datetime as dt
from email.mime.text import MIMEText
from email.header import Header

import feedparser

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.126.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
MAIL_TO = os.getenv("MAIL_TO", "harrywong2005@126.com")

FEEDS = [
    # 中文搜索
    "https://news.google.com/rss/search?q=%E7%BC%96%E7%A0%81%E5%99%A8&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "https://news.google.com/rss/search?q=%E6%97%8B%E8%BD%AC%E7%BC%96%E7%A0%81%E5%99%A8&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "https://news.google.com/rss/search?q=%E7%BB%9D%E5%AF%B9%E5%80%BC%E7%BC%96%E7%A0%81%E5%99%A8&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "https://news.google.com/rss/search?q=%E7%A3%81%E7%BC%96%E7%A0%81%E5%99%A8&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "https://news.google.com/rss/search?q=%E4%BC%BA%E6%9C%8D%E7%BC%96%E7%A0%81%E5%99%A8&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "https://news.google.com/rss/search?q=%E4%BD%8D%E7%BD%AE%E4%BC%A0%E6%84%9F%E5%99%A8&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    # 英文新品
    "https://news.google.com/rss/search?q=encoder+new+product&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=rotary+encoder+launch&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=absolute+encoder+introduces&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=magnetic+encoder+unveils&hl=en-US&gl=US&ceid=US:en",
    # 行业媒体
    "https://spectrum.ieee.org/feeds/topic/robotics.rss",
    "https://www.therobotreport.com/feed/",
    "https://www.controleng.com/feed/",
    "https://www.designworldonline.com/feed/",
    "https://www.eetimes.com/feed/",
    "https://www.edn.com/feed/",
    "https://www.automationworld.com/rss.xml",
]

ENCODER_KW = [
    "编码器", "旋转编码器", "绝对值编码器", "增量式编码器", "磁编码器", "光编码器",
    "光电编码器", "电容编码器", "电感编码器", "中空轴", "多圈", "单圈", "伺服编码器",
    "电机编码器", "位置传感器", "角度传感器", "旋变", "多摩川", "海德汉", "雷尼绍",
    "堡盟", "西克", "倍加福", "图尔克", "易福门", "库伯勒", "禹衡", "奥通", "瑞普",
    "汇川", "禾川", "埃斯顿", "鸣志", "雷赛", "步科", "纳芯微", "赛卓", "麦歌恩",
    "多维科技", "矽睿", "明皜",
    "encoder", "rotary encoder", "absolute encoder", "incremental encoder",
    "magnetic encoder", "optical encoder", "capacitive encoder", "inductive encoder",
    "hollow shaft", "multi-turn", "single-turn", "servo encoder", "motor encoder",
    "position sensor", "angle sensor", "resolver", "biss", "endat", "hiperface",
    "ssi", "tamagawa", "heidenhain", "renishaw", "baumer", "sick",
    "pepperl+fuchs", "turck", "ifm", "posital", "fraba", "kubler", "siko",
    "tr electronic", "leine linde", "lenord+bauer", "wachendorff", "hengstler",
    "dynapar", "encoder products", "us digital", "cui devices", "broadcom",
    "ic-haus", "netzer", "zettlex", "celera motion", "gurley",
]

NEW_KW = [
    "新品", "发布", "推出", "上市", "量产", "新一代", "全新", "升级", "首发",
    "亮相", "问世", "面世", "开售", "发售", "投产", "下线", "交付", "新系列",
    "新产品", "新型", "新方案", "新平台",
    "launch", "launches", "launched", "new", "introduces", "introduced",
    "unveils", "unveiled", "release", "released", "product", "series",
    "next-gen", "next generation", "debuts", "available", "sampling",
    "mass production",
]

TECH_KW = [
    "技术", "原理", "方案", "设计", "算法", "精度", "分辨率", "抗干扰",
    "可靠性", "校准", "补偿", "technology", "design", "algorithm",
    "accuracy", "resolution", "calibration",
]

MARKET_KW = [
    "市场", "融资", "收购", "并购", "财报", "营收", "出货", "份额", "趋势",
    "预测", "报告", "market", "funding", "acquisition", "merger", "revenue",
    "shipment", "forecast", "report",
]

PAPER_KW = [
    "论文", "研究", "专利", "学术", "期刊", "ieee", "arxiv", "白皮书",
    "paper", "patent", "study", "research", "journal", "conference",
]

def hit(text, kws):
    t = text.lower()
    return any(k.lower() in t for k in kws)

def score_item(title, summary):
    text = f"{title} {summary}"
    s = 0
    if hit(title, NEW_KW):
        s += 12
    elif hit(summary, NEW_KW):
        s += 6
    if hit(title, ENCODER_KW):
        s += 8
    elif hit(summary, ENCODER_KW):
        s += 4
    if hit(text, PAPER_KW):
        s += 2
    if hit(text, MARKET_KW):
        s += 1
    return s

def classify(title, summary):
    text = f"{title} {summary}"
    if hit(text, NEW_KW):
        return "新品"
    if hit(text, PAPER_KW):
        return "论文专利"
    if hit(text, MARKET_KW):
        return "市场"
    if hit(text, TECH_KW):
        return "技术"
    return "其他"

items = []

for feed_url in FEEDS:
    try:
        feed = feedparser.parse(feed_url)
        source = feed.feed.get("title", feed_url)

        for e in feed.entries[:30]:
            title = e.get("title", "")
            summary = e.get("summary", "") or e.get("description", "")
            link = e.get("link", "")

            if not link or not title:
                continue

            text = f"{title} {summary}"
            if not hit(text, ENCODER_KW):
                continue

            sc = score_item(title, summary)
            if sc <= 0:
                continue

            published = e.get("published", "") or e.get("updated", "")
            ts = 0

            if getattr(e, "published_parsed", None):
                ts = dt.datetime(*e.published_parsed[:6], tzinfo=dt.timezone.utc).timestamp()
            elif getattr(e, "updated_parsed", None):
                ts = dt.datetime(*e.updated_parsed[:6], tzinfo=dt.timezone.utc).timestamp()

            items.append({
                "title": title.strip(),
                "link": link,
                "summary": re.sub("<[^>]+>", "", summary)[:220],
                "source": source,
                "published": published,
                "ts": ts,
                "score": sc,
                "cat": classify(title, summary),
            })

    except Exception as ex:
        print("feed error:", feed_url, ex)

# 去重 + 新品优先排序
seen = set()
uniq = []

for it in sorted(items, key=lambda x: (x["score"], x["ts"]), reverse=True):
    key = re.sub(r"\W+", "", it["title"].lower())[:80] or it["link"]
    if key in seen:
        continue
    seen.add(key)
    uniq.append(it)

cat_order = ["新品", "技术", "市场", "论文专利", "其他"]
grouped = {c: [] for c in cat_order}

for it in uniq:
    c = it["cat"] if it["cat"] in grouped else "其他"
    if len(grouped[c]) < 8:
        grouped[c].append(it)

today = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).strftime("%Y-%m-%d")

parts = [
    f"<h2>编码器每日简报 {today}（新品优先·中文）</h2>",
    "<p>覆盖：编码器 / 旋转编码器 / 绝对值 / 磁/光/电容/电感 / 伺服电机编码器 / "
    "位置角度传感器 / 运动控制 / 机器人 / 伺服。</p >",
]

for c in cat_order:
    arr = grouped.get(c, [])
    if not arr:
        continue

    parts.append(f"<h3>{c}</h3><ol>")

    for it in arr:
        title = html.escape(it["title"])
        summary = html.escape(it["summary"]).replace("&amp;",""")
        source = html.escape(it["source"])
        pub = html.escape(it["published"])

        parts.append(
            f'<li><a href=" {link}"target="blank">{title}</a >'
            f'<br><small>{source} {pub}</small>'
            f'<br>{summary}</li>'
        )

    parts.append("</ol>")

if not any(grouped.values()):
    parts.append("<p>今天没有抓到匹配条目，可能是源暂时不可用或关键词过窄。</p >")

parts.append("<p>由自动脚本生成。</p >")
html_body = "\n".join(parts)

if not SMTP_USER or not SMTP_PASS:
    raise SystemExit("缺少 SMTP_USER / SMTP_PASS")

msg = MIMEText(html_body, "html", "utf-8")
msg["Subject"] = Header(f"编码器每日简报 {today}｜新品优先", "utf-8")
msg["From"] = SMTP_USER
msg["To"] = MAIL_TO

with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
    server.login(SMTP_USER, SMTP_PASS)
    server.sendmail(SMTP_USER, [MAIL_TO], msg.as_string())

print("sent to", MAIL_TO)

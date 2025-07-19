import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin

def generate():
    url = "https://verstka.media/category/article"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select("li.wp-block-post")

    fg = FeedGenerator()
    fg.title("Верстка — Статьи")
    fg.link(href=url, rel="alternate")
    fg.description("Новые статьи от издания Верстка")
    fg.language("ru")

    for item in items:
        a_el = item.select_one("h3 a")
        if not a_el:
            continue
        title = a_el.text.strip()
        link = a_el.get("href")
        pubdate_el = item.select_one("time")
        pubdate_str = pubdate_el.get("datetime") if pubdate_el else ""
        try:
            pubDate = datetime.fromisoformat(pubdate_str)
        except:
            pubDate = datetime.now()

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(title)
        fe.pubDate(pubDate)

    fg.rss_file("feed_verstka.xml")

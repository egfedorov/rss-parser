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

    # Новая структура — работает
    items = soup.select("li.wp-block-post")

    fg = FeedGenerator()
    fg.title("Верстка — Статьи")
    fg.link(href=url, rel="alternate")
    fg.description("Новые статьи от издания Верстка")
    fg.language("ru")

    for item in items:
        # Новый главный селектор
        a_el = item.select_one(".wp-block-post-title a")
        if not a_el:
            continue     # пропускаем рекламное видео

        title = a_el.get_text(strip=True)
        link = a_el.get("href")

        # дата
        time_el = item.select_one("time[datetime]")
        if time_el:
            dt_raw = time_el["datetime"]
            try:
                pubDate = datetime.fromisoformat(dt_raw)
            except:
                pubDate = datetime.now(timezone.utc)
        else:
            pubDate = datetime.now(timezone.utc)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(title)
        fe.pubDate(pubDate)

    fg.rss_file("verstka.xml")

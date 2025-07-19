import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin

def generate():
    url = "https://holod.media/obshhestvo/"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("div.news-card")

    fg = FeedGenerator()
    fg.title("Холод — Общество")
    fg.link(href=url, rel="alternate")
    fg.description("Статьи из раздела 'Общество' на сайте Холод")
    fg.language("ru")

    for art in articles:
        title_el = art.select_one("div.news-card__title a")
        if not title_el:
            continue

        title = title_el.text.strip()
        link = title_el.get("href")
        description_el = art.select_one("div.news-card__desc")
        description = description_el.text.strip() if description_el else ""
        date_el = art.select_one("div.news-card__date")
        date_str = date_el.text.strip() if date_el else ""

        # Парсинг даты: формат "00:01 15 июля"
        try:
            time_part, day, month_str = date_str.split()
            hour, minute = map(int, time_part.split(":"))
            day = int(day)

            months = {
                "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
                "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
            }
            month = months.get(month_str.lower(), 1)
            now = datetime.now(timezone.utc)
            pub_date = datetime(now.year, month, day, hour, minute, tzinfo=timezone.utc)
        except Exception:
            pub_date = datetime.now(timezone.utc)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.pubDate(pub_date)

    fg.rss_file("feed_holod.xml")

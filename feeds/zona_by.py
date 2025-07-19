import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin

def parse_date(date_str):
    months = {
        "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
        "мая": 5, "июня": 6, "июля": 7, "августа": 8,
        "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
    }
    try:
        parts = date_str.strip().split()
        if "," in parts[0]:
            # формат: "2 июля 2025, 13:57"
            day, month, year = int(parts[0]), months[parts[1]], int(parts[2][:-1])
            time_part = parts[3]
        else:
            # формат: "17 июля 2025, 21:03"
            day, month, year = int(parts[0]), months[parts[1]], int(parts[2].strip(","))
            time_part = parts[3]
        hour, minute = map(int, time_part.split(":"))
        return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    except:
        return datetime.now(timezone.utc)

def generate():
    url = "https://mediazonaby.com/texts"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select("li.mz-material-item, section.mz-feature-item")

    fg = FeedGenerator()
    fg.title("Медиазона.Беларусь")
    fg.link(href=url, rel="alternate")
    fg.description("Статьи и репортажи")
    fg.language("ru")

    for item in items:
        link_el = item.select_one("a[href^='/article/']")
        title_el = item.select_one("header")
        date_el = item.select_one("span.mz-content-meta-info__item:nth-last-child(1)")

        if not link_el or not title_el:
            continue

        link = urljoin(url, link_el["href"])
        title = title_el.get_text(strip=True)
        description = ""
        if item.select_one("p"):
            description = item.select_one("p").get_text(strip=True)
        elif item.select_one("div.mz-material-item__announce-text"):
            description = item.select_one("div.mz-material-item__announce-text").get_text(strip=True)

        date = parse_date(date_el.get_text(strip=True)) if date_el else datetime.now()

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.pubDate(date)

    fg.rss_file("zona_by.xml")

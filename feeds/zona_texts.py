import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin
import re

def parse_date(date_str):
    months = {
        "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
        "мая": 5, "июня": 6, "июля": 7, "августа": 8,
        "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
    }
    try:
        # Пример: "3 ноября 2025, 11:35"
        parts = date_str.strip().replace(",", "").split()
        day = int(parts[0])
        month = months[parts[1]]
        year = int(parts[2])
        time_part = parts[3]
        hour, minute = map(int, time_part.split(":"))
        return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def extract_background_url(style_str):
    """Извлекает ссылку из background-image: url("...")"""
    if not style_str:
        return None
    match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style_str)
    return match.group(1) if match else None

def generate():
    url = "https://zona.media/texts"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select("article.feed-itemarticle")

    fg = FeedGenerator()
    fg.title("Zona Media — Тексты")
    fg.link(href=url, rel="alternate")
    fg.description("Статьи и репортажи Zona Media")
    fg.language("ru")

    for item in items:
        link_el = item.select_one("a.feed-item__link")
        title_el = item.select_one("h2.feed-item__title, h3.feed-item__title")
        date_el = item.select_one("time.feed-item__date")

        if not link_el or not title_el:
            continue

        link = urljoin(url, link_el["href"])
        title = title_el.get_text(strip=True)
        date = parse_date(date_el.get_text(strip=True)) if date_el else datetime.now(timezone.utc)

        # описание пока не указано на сайте
        description = ""

        # пробуем извлечь изображение
        img_url = None
        img_tag = item.select_one("img")
        if img_tag and img_tag.get("src"):
            img_url = img_tag["src"]
        else:
            img_url = extract_background_url(item.get("style"))

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.pubDate(date)
        if img_url:
            fe.enclosure(img_url, 0, "image/jpeg")

    fg.rss_file("feed_zona_texts.xml")

if __name__ == "__main__":
    generate()

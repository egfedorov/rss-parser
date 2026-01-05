import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import time
import re

BASE = "https://72.ru"

MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
}

def parse_date(s):
    m = re.search(r'(\d{1,2})\s+([а-яё]+),?\s*(\d{4}),?\s*(\d{1,2}):(\d{2})', s.lower())
    d, mon, y, h, mi = m.groups()
    return datetime(int(y), MONTHS[mon], int(d), int(h), int(mi), tzinfo=timezone.utc)

def generate():
    ts = int(time.time() * 1000)
    url = f"https://72.ru/text/author/159611/?_dc={ts}"

    print("[INFO] Загружаем реальный URL:", url)

    r = requests.get(url, headers=HEADERS, timeout=15)
    r.encoding = "utf-8"

    print("[INFO] HTTP status:", r.status_code)
    print("[INFO] HTML length:", len(r.text))

    soup = BeautifulSoup(r.text, "html.parser")
    articles = soup.find_all("article")

    print("[INFO] Найдено статей:", len(articles))

    if not articles:
        print("[FATAL] HTML загружен, но статей нет. Проверить timestamp URL.")
        return

    fg = FeedGenerator()
    fg.title("72.ru — Малышкина")
    fg.link(href="https://72.ru/text/author/159611/")
    fg.description("Публикации автора на 72.ru")

    for art in articles:
        title_tag = art.select_one('a[class*="header"] span')
        link_tag = art.find("a", href=True)
        date_tag = art.select_one("span[class*='text']")

        if not (title_tag and link_tag and date_tag):
            continue

        title = title_tag.get_text(strip=True)
        link = link_tag["href"]
        if link.startswith("/"):
            link = BASE + link

        pubdate = parse_date(date_tag.get_text(strip=True))

        img_tag = art.select_one("picture img")
        img = img_tag["src"] if img_tag else None

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pubdate)
        if img:
            fe.enclosure(img, 0, "image/jpeg")

    fg.rss_file("malyshkina.xml", encoding="utf-8")
    print("[OK] RSS создан")

if __name__ == "__main__":
    generate()

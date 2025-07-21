import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re
from urllib.parse import urljoin

MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

def parse_date(text, current_year=None, current_month=None, current_day=None):
    """
    Универсальный парсер даты:
    - "00:01 19 июля"
    - "14:33"
    - "19:19 20 июля"
    """
    text = text.strip()
    now = datetime.now(timezone.utc)
    if not current_year:
        current_year = now.year

    m = re.match(r'(\d{1,2}):(\d{2})(?:\s+(\d{1,2})\s+([а-я]+))?', text)
    if m:
        hour, minute, day, month_str = m.groups()
        hour = int(hour)
        minute = int(minute)
        if day and month_str:
            day = int(day)
            month = MONTHS.get(month_str.lower(), now.month)
            return datetime(current_year, month, day, hour, minute, tzinfo=timezone.utc)
        else:
            # Если нет дня/месяца, берём текущую дату (можно доработать!)
            if current_month and current_day:
                return datetime(current_year, current_month, current_day, hour, minute, tzinfo=timezone.utc)
            return datetime(current_year, now.month, now.day, hour, minute, tzinfo=timezone.utc)
    else:
        # fallback: текущее время
        return now

def generate():
    url = "https://holod.media/obshhestvo/"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    fg = FeedGenerator()
    fg.title("Холод — Общество")
    fg.link(href=url, rel="alternate")
    fg.description("Статьи из раздела 'Общество' на сайте Холод")
    fg.language("ru")

    # 1. news-card (основные материалы)
    articles = soup.select(".news-card")
    for art in articles:
        title_el = art.select_one(".news-card__title a")
        if not title_el:
            continue

        title = title_el.text.strip()
        link = title_el.get("href")
        link = urljoin(url, link)
        description_el = art.select_one(".news-card__desc")
        description = description_el.text.strip() if description_el else ""
        date_el = art.select_one(".news-card__date")
        date_str = date_el.text.strip() if date_el else ""
        pub_date = parse_date(date_str)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.pubDate(pub_date)

    # 2. hero-card (центральная большая карточка, если есть)
    hero = soup.select_one(".hero-card")
    if hero:
        title_el = hero.select_one(".hero-card__title")
        link = hero.get("href")
        title = title_el.text.strip() if title_el else ""
        link = urljoin(url, link)
        description_el = hero.select_one(".hero-card__desc")
        description = description_el.text.strip() if description_el else ""
        date_el = hero.select_one(".hero-card__date")
        date_str = date_el.text.strip() if date_el else ""
        pub_date = parse_date(date_str)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.pubDate(pub_date)

    # 3. text-card (маленькие карточки), кроме тех что внутри .hero-catalog__right
    all_text_cards = soup.select(".text-card")
    right_block = soup.select_one(".hero-catalog__right")
    right_text_cards = set()
    if right_block:
        right_text_cards = set(right_block.select(".text-card"))

    for card in all_text_cards:
        if card in right_text_cards:
            continue  # Пропускаем карточки из блока hero-catalog__right

        link = card.get("href")
        link = urljoin(url, link)
        description_el = card.select_one(".text-card__desc")
        description = description_el.text.strip() if description_el else ""
        title = description
        date_el = card.select_one(".text-card__date")
        date_str = date_el.text.strip() if date_el else ""
        pub_date = parse_date(date_str)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.pubDate(pub_date)

    fg.rss_file("feed_holod.xml")

if __name__ == "__main__":
    generate()

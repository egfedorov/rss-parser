import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin
from datetime import datetime, timezone
import re

MONTHS_RU = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

def parse_russian_date(date_str):
    """Парсит дату типа '17 июля 2025' в datetime с UTC"""
    parts = date_str.strip().split()
    if len(parts) != 3:
        return None
    try:
        day = int(parts[0])
        month = MONTHS_RU[parts[1].lower()]
        year = int(parts[2])
        # Всегда полночь, но с указанием UTC
        return datetime(year, month, day, tzinfo=timezone.utc)
    except Exception:
        return None

def generate():
    url = "https://daily.afisha.ru/authors/svetlana-burakova/"
    base_url = "https://daily.afisha.ru"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    fg = FeedGenerator()
    fg.title("Afisha Daily — Светлана Буракова")
    fg.link(href=url, rel="alternate")
    fg.description("Публикации автора с сайта daily.afisha.ru")
    fg.language("ru")

    for card in soup.select('a.RowCard_Container__BwANN'):
        link = urljoin(base_url, card["href"])
        # Название (h6)
        title_tag = card.find("h6")
        title = title_tag.get_text(strip=True) if title_tag else card.get("title", "").strip() or card.text.strip()
        # Дата публикации (span с классом RowCard_DateLabel___QZN8)
        date_span = card.select_one('span.RowCard_DateLabel___QZN8')
        pub_date = None
        if date_span:
            pub_date = parse_russian_date(date_span.text)
        # Описание (по желанию — если нужно)
        desc = ""
        desc_tag = card.find("span", class_="RowCard_ThemeName__uTji_")
        if desc_tag:
            desc = desc_tag.get_text(strip=True)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(desc)
        if pub_date:
            fe.pubDate(pub_date)

    fg.rss_file("burakova.xml")

if __name__ == "__main__":
    generate()

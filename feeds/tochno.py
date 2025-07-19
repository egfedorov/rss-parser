import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin
import re

MONTHS = {
    'января': 1,
    'февраля': 2,
    'марта': 3,
    'апреля': 4,
    'мая': 5,
    'июня': 6,
    'июля': 7,
    'августа': 8,
    'сентября': 9,
    'октября': 10,
    'ноября': 11,
    'декабря': 12,
}

def parse_date(date_str: str) -> datetime:
    """
    Преобразует "17 июля" в datetime с текущим годом и таймзоной UTC.
    """
    try:
        parts = date_str.strip().split()
        day = int(parts[0])
        month = MONTHS.get(parts[1].lower(), 1)
        year = datetime.now().year  # можно заменить на другой при необходимости
        return datetime(year, month, day, tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def generate():
    url = 'https://tochno.st/materials?problem_path=all&tags=all&sort_by=new&type=all&year=all#LibraryFilterPanel'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Точно.ст — Материалы')
    fg.link(href=url, rel='alternate')
    fg.description('Все материалы с сайта tochno.st')
    fg.language('ru')

    cards = soup.select('.b-material-card')

    for card in cards:
        link_tag = card.select_one('a.b-material-card__link')
        date_tags = card.select('.b-material-card__type')  # Дата — обычно второй тег
        title = link_tag.get_text(strip=True) if link_tag else None
        link = urljoin(url, link_tag['href']) if link_tag else None
        date_str = date_tags[1].get_text(strip=True) if len(date_tags) > 1 else ''
        pub_date = parse_date(date_str)

        if not (title and link):
            continue

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pub_date)

    fg.rss_file('tochno.xml')

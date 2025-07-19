import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin
import re

MONTHS = {
    'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4, 'май': 5, 'июнь': 6,
    'июль': 7, 'август': 8, 'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12,
}

def parse_date(date_str: str) -> datetime:
    # Июль 18, 2025
    match = re.match(r"([А-Яа-я]+)\s+(\d{1,2}),\s*(\d{4})", date_str.strip())
    if match:
        month = MONTHS.get(match.group(1).lower(), 1)
        day = int(match.group(2))
        year = int(match.group(3))
        return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
    # fallback
    return datetime.now(timezone.utc)

def generate():
    url = 'https://www.idelreal.org/interview'
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Idel.Реалии — Интервью')
    fg.link(href=url, rel='alternate')
    fg.description('Все интервью с сайта Idel.Реалии')
    fg.language('ru')

    cards = soup.select('ul.archive-list li.archive-list__item')
    for card in cards:
        title_tag = card.select_one('.media-block__title')
        title = title_tag.text.strip() if title_tag else None

        link_tag = card.select_one('a[href*="/a/"]')
        link = urljoin(url, link_tag['href']) if link_tag else None

        date_tag = card.select_one('.date')
        date_str = date_tag.text.strip() if date_tag else None

        if not title or not date_str or not link:
            continue

        pub_date = parse_date(date_str)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pub_date)

    fg.rss_file('idel_int.xml')

if __name__ == '__main__':
    generate()

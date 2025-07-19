import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin
import re

MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
    'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}

def parse_date(date_str: str) -> datetime:
    # "01 июля 2025" → datetime(2025, 7, 1, 12, 0, tzinfo=timezone.utc)
    match = re.match(r"(\d{1,2}) (\w+) (\d{4})", date_str.strip())
    if match:
        day = int(match.group(1))
        month = MONTHS.get(match.group(2).lower(), 1)
        year = int(match.group(3))
        return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def generate():
    url = 'https://www.svoboda.org/author/%D0%B5%D0%B2%D0%B3%D0%B5%D0%BD%D0%B8%D0%B9-%D0%BB%D0%B5%D0%B3%D0%B0%D0%BB%D0%BE%D0%B2/mjrkqm'
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Свобода — Евгений Легалов')
    fg.link(href=url, rel='alternate')
    fg.description('Все публикации Евгения Легалова на svoboda.org')
    fg.language('ru')

    cards = soup.select('li.mb-grid.archive-list__item')

    for card in cards:
        # Заголовок и ссылка
        title_tag = card.select_one('.media-block__title')
        title = title_tag.text.strip() if title_tag else None

        link_tag = card.select_one('.media-block a.img-wrap')
        link = urljoin(url, link_tag['href']) if link_tag and link_tag.has_attr('href') else None

        # Дата
        date_tag = card.select_one('.date')
        date_str = date_tag.text.strip() if date_tag else None
        pub_date = parse_date(date_str) if date_str else None

        if not title or not link or not pub_date:
            continue

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pub_date)

    fg.rss_file('legalov.xml')

if __name__ == '__main__':
    generate()

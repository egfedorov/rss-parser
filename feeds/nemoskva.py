import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
    'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}

def parse_date(date_str: str) -> datetime:
    # "18 июля 2025" => datetime(2025, 7, 18, 12, 0, tzinfo=timezone.utc)
    match = re.match(r"(\d{1,2}) (\w+) (\d{4})", date_str.strip())
    if match:
        day = int(match.group(1))
        month = MONTHS.get(match.group(2).lower(), 1)
        year = int(match.group(3))
        return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def generate():
    url = 'https://nemoskva.net/stories/'
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Nemoskva — Истории')
    fg.link(href=url, rel='alternate')
    fg.description('Все истории с сайта nemoskva.net')
    fg.language('ru')

    cards = soup.select('.ultp-block-item')

    for card in cards:
        title_tag = card.select_one('h3.ultp-block-title a')
        title = title_tag.text.strip() if title_tag else None
        link = title_tag['href'] if title_tag else None

        date_tag = card.select_one('.ultp-block-date')
        date_str = date_tag.text.strip() if date_tag else None

        desc_tag = card.select_one('.ultp-block-excerpt')
        description = desc_tag.text.strip() if desc_tag else None

        if not title or not date_str or not link:
            continue

        pub_date = parse_date(date_str)
        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pub_date)
        if description:
            fe.description(description)

    fg.rss_file('nemoskva.xml')

if __name__ == '__main__':
    generate()

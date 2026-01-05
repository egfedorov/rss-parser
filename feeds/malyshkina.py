import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

URL = 'https://72.ru/text/author/159611/'
BASE = 'https://72.ru'

MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; RSSBot/1.0)'
}


def parse_date(date_str: str) -> datetime:
    """
    '1 января, 2026, 06:02' -> datetime UTC
    """
    m = re.search(
        r'(\d{1,2})\s+([а-яё]+),?\s*(\d{4}),?\s*(\d{1,2}):(\d{2})',
        date_str.lower()
    )
    if not m:
        raise ValueError(f'Не удалось распарсить дату: {date_str}')

    day, month_str, year, hour, minute = m.groups()
    return datetime(
        int(year),
        MONTHS[month_str],
        int(day),
        int(hour),
        int(minute),
        tzinfo=timezone.utc
    )


def generate():
    r = requests.get(URL, headers=HEADERS, timeout=15)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('72.ru — публикации автора')
    fg.link(href=URL, rel='alternate')
    fg.description('Публикации автора на 72.ru')
    fg.language('ru')

    articles = soup.find_all('article')
    print(f'[INFO] Найдено статей: {len(articles)}')

    for art in articles:
        # ссылка
        link_tag = art.find('a', href=True)
        if not link_tag:
            continue

        link = link_tag['href']
        if link.startswith('/'):
            link = BASE + link

        # заголовок
        title_tag = art.select_one('a[class*="header"] span')
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)

        # дата
        date_tag = art.select_one('span[class*="text"]')
        if not date_tag:
            continue

        try:
            pub_date = parse_date(date_tag.get_text(strip=True))
        except Exception as e:
            print(f'[WARN] {e}')
            continue

        # картинка
        img_tag = art.select_one('picture img')
        img_url = img_tag['src'] if img_tag else None

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pub_date)

        if img_url:
            fe.enclosure(img_url, 0, 'image/jpeg')

    fg.rss_file('malyshkina.xml', encoding='utf-8')
    print('[OK] RSS создан')


if __name__ == '__main__':
    generate()

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}

def parse_date(date_str: str) -> datetime | None:
    """
    '11 июля, 2025, 17:21' / '11 июля 2025, 17:21'
    """
    if not date_str:
        return None

    m = re.search(
        r'(\d{1,2})\s+([а-яё]+)\s*,?\s*(\d{4})\s*,?\s*(\d{1,2}):(\d{2})',
        date_str.lower()
    )
    if not m:
        return None

    day, month_name, year, hour, minute = m.groups()
    month = MONTHS.get(month_name)
    if not month:
        return None

    return datetime(
        int(year),
        month,
        int(day),
        int(hour),
        int(minute),
        tzinfo=timezone.utc
    )

def generate():
    url = 'https://72.ru/text/author/159611/'
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('72.ru — публикации Малышкиной')
    fg.link(href=url, rel='alternate')
    fg.description('Материалы автора на 72.ru')
    fg.language('ru')

    # Все материалы автора — это article внутри main
    articles = soup.select('main article')

    if not articles:
        print('[WARN] Не найдено ни одной статьи')

    for art in articles:
        # ссылка
        link_tag = art.select_one('a[href]')
        if not link_tag:
            continue

        link = link_tag['href']
        if link.startswith('/'):
            link = 'https://72.ru' + link

        # заголовок
        title_tag = art.select_one('a h2, a span')
        title = title_tag.get_text(strip=True) if title_tag else None
        if not title:
            continue

        # дата
        date_text = None

        # чаще всего дата лежит в span рядом с иконкой времени
        for span in art.select('span'):
            txt = span.get_text(strip=True)
            if txt and re.search(r'\d{4}.*\d{1,2}:\d{2}', txt):
                date_text = txt
                break

        pub_date = parse_date(date_text)

        fe = fg.add_entry()
        fe.id(link)          # КРИТИЧНО для дедупликации
        fe.title(title)
        fe.link(href=link)

        if pub_date:
            fe.pubDate(pub_date)

        # картинка (если есть)
        img = art.select_one('img[src]')
        if img:
            img_url = img['src']
            if img_url.startswith('/'):
                img_url = 'https://72.ru' + img_url
            fe.enclosure(img_url, 0, 'image/jpeg')

    fg.rss_file('malyshkina.xml', encoding='utf-8')
    print(f'[OK] Сформирован RSS: {len(fg.entry())} записей')

if __name__ == '__main__':
    generate()

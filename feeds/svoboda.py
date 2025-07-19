import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

# Парсим "16 июля 2025"
def parse_svoboda_date(date_str):
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
        'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    m = re.match(r'(\d{1,2}) ([а-яё]+) (\d{4})', date_str.strip(), re.I)
    if m:
        day, month_str, year = m.groups()
        month = months.get(month_str.lower())
        if month:
            return datetime(int(year), month, int(day), 12, 0, tzinfo=timezone.utc)
    # Если не получилось, вернуть сейчас
    return datetime.now(timezone.utc)

def generate():
    url = 'https://www.svoboda.org/investigations'
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Радио Свобода — Расследования')
    fg.link(href=url, rel='alternate')
    fg.description('Расследования Радио Свобода')
    fg.language('ru')

    for li in soup.select('ul.archive-list > li.archive-list__item'):
        # Дата
        date_tag = li.select_one('span.date')
        date_str = date_tag.get_text(strip=True) if date_tag else ''
        pub_date = parse_svoboda_date(date_str) if date_str else datetime.now(timezone.utc)
        # Ссылка
        a_tag = li.select_one('a[href*=".html"]')
        if not a_tag:
            continue
        href = a_tag['href']
        if not href.startswith('http'):
            href = 'https://www.svoboda.org' + href
        # Заголовок
        title_tag = li.select_one('h4')
        title = title_tag.get_text(strip=True) if title_tag else 'Без названия'
        # Картинка
        img_tag = li.select_one('img.enhanced')
        image = img_tag['src'] if img_tag and img_tag.has_attr('src') else ''
        # Описание — заголовок
        description = title

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=href)
        fe.pubDate(pub_date)
        fe.description(description)
        if image:
            fe.enclosure(image, 0, 'image/jpeg')

    fg.rss_file('svoboda.xml')

if __name__ == '__main__':
    generate()

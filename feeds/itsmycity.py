import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

def parse_date_itsmycity(date_str):
    # Поддержка: '15 июля, 15:31, 2025 г.' | '15 июля, 2025 г.' | '19 июля, 16:21'
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    date_str = date_str.strip()
    # 1. Полная дата с годом и временем
    m = re.match(r"(\d{1,2}) ([а-яё]+), (\d{2}):(\d{2}), (\d{4}) г\.", date_str)
    if m:
        day, month_str, hour, minute, year = m.groups()
        try:
            month = months[month_str]
            return datetime(int(year), month, int(day), int(hour), int(minute), tzinfo=timezone.utc)
        except Exception as e:
            print(f'❌ Ошибка разбора даты: {date_str}: {e}')
            return datetime.now(timezone.utc)
    # 2. Только дата с годом
    m = re.match(r"(\d{1,2}) ([а-яё]+), (\d{4}) г\.", date_str)
    if m:
        day, month_str, year = m.groups()
        try:
            month = months[month_str]
            return datetime(int(year), month, int(day), 12, 0, tzinfo=timezone.utc)
        except Exception as e:
            print(f'❌ Ошибка разбора даты: {date_str}: {e}')
            return datetime.now(timezone.utc)
    # 3. Только дата и время (год = текущий)
    m = re.match(r"(\d{1,2}) ([а-яё]+), (\d{2}):(\d{2})", date_str)
    if m:
        day, month_str, hour, minute = m.groups()
        try:
            now = datetime.now(timezone.utc)
            month = months[month_str]
            return datetime(now.year, month, int(day), int(hour), int(minute), tzinfo=timezone.utc)
        except Exception as e:
            print(f'❌ Ошибка разбора даты: {date_str}: {e}')
            return datetime.now(timezone.utc)
    print(f'❌ Не удалось распознать дату: {date_str}')
    return datetime.now(timezone.utc)

def generate():
    url = 'https://itsmycity.ru/sections/people'
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('ItsMyCity — Люди')
    fg.link(href=url, rel='alternate')
    fg.description('Раздел «Люди» городского портала ItsMyCity')
    fg.language('ru')

    for card in soup.select('.imc-col-card a'):
        href = card.get('href')
        abs_url = href if href.startswith('http') else 'https://itsmycity.ru' + href

        # Картинка (опционально)
        img_tag = card.select_one('img.lazyload')
        image = img_tag.get('data-src') if img_tag else ''

        # Заголовок
        title_tag = card.select_one('.imc-card-title')
        title = title_tag.get_text(strip=True) if title_tag else 'Без названия'

        # Описание (первый <p>)
        desc_tag = card.select_one('p.imc-card-text')
        description = desc_tag.get_text(strip=True) if desc_tag else ''

        # Дата
        date_tag = card.select_one('.imc-card-date')
        date_str = date_tag.get_text(strip=True) if date_tag else ''
        pub_date = parse_date_itsmycity(date_str) if date_str else datetime.now(timezone.utc)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=abs_url)
        if description:
            fe.description(description)
        fe.pubDate(pub_date)
        if image:
            fe.enclosure(image, 0, 'image/jpeg')

    fg.rss_file('itsmycity.xml')

if __name__ == '__main__':
    generate()

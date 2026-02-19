import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

def parse_date_ngs(date_str):
    # Пример: "19 июля, 2025, 10:00"
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
        'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    m = re.match(r'(\d{1,2}) ([а-я]+), (\d{4}), (\d{2}):(\d{2})', date_str.strip(), re.I)
    if m:
        day, month_str, year, hour, minute = m.groups()
        month = months.get(month_str.lower(), 1)
        return datetime(int(year), month, int(day), int(hour), int(minute), tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def generate():
    return
    
    url = 'https://msk1.ru/text/format/reportage/'
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('MSK1 — Репортажи')
    fg.link(href=url, rel='alternate')
    fg.description('Репортажи')
    fg.language('ru')

    for post in soup.select('.wrap_RL97A'):
        # Ссылка и изображение
        a_tag = post.select_one('.imgBg_RL97A')
        link = a_tag['href'] if a_tag else None
        if link and not link.startswith('http'):
            link = 'https://msk1,ru' + link

        img_tag = post.select_one('img.image_RL97A')
        image = img_tag['src'] if img_tag else None

        # Дата публикации
        date_tag = post.select_one('.cell_eiDCU .text_eiDCU')
        pub_date = parse_date_ngs(date_tag.get_text(strip=True)) if date_tag else datetime.now(timezone.utc)

        # Заголовок
        title_tag = post.select_one('.header_RL97A')
        title = title_tag.get_text(strip=True) if title_tag else 'Без названия'

        # Описание
        description = a_tag['title'] if a_tag and a_tag.has_attr('title') else ''

        fe = fg.add_entry()
        fe.title(title)
        if link:
            fe.link(href=link)
        fe.pubDate(pub_date)
        if description:
            fe.description(description)
        if image:
            fe.enclosure(image, 0, 'image/jpeg')

    fg.rss_file('msk1.xml')

if __name__ == '__main__':
    generate()

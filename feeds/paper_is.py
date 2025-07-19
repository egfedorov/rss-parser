import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

def parse_date_paperpaper(date_str):
    # Пример: '15 июля 2025'
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    m = re.match(r'(\d{1,2}) ([а-яё]+) (\d{4})', date_str.strip())
    if m:
        day, month_str, year = m.groups()
        month = months.get(month_str, 1)
        return datetime(int(year), month, int(day), 12, 0, tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def generate():
    url = 'https://paperpaper.io/category/researches/'
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Бумага — Исследования')
    fg.link(href=url, rel='alternate')
    fg.description('Раздел сайта Бумага')
    fg.language('ru')

    for post in soup.select('.post'):
        # Ссылка и изображение
        a_tag = post.select_one('.post__img a')
        link = a_tag['href'] if a_tag else None
        if link and not link.startswith('http'):
            link = 'https://paperpaper.io' + link

        img_tag = post.select_one('.post__img img')
        image = img_tag['src'] if img_tag else None

        # Дата публикации
        date_tag = post.select_one('.post__date')
        pub_date = parse_date_paperpaper(date_tag.get_text(strip=True)) if date_tag else datetime.now(timezone.utc)

        # Рубрика (можно добавить к description)
        tag = post.select_one('.post__tag a')
        rubric = tag.get_text(strip=True) if tag else None

        # Заголовок
        title_tag = post.select_one('.post__title')
        title = title_tag.get_text(strip=True) if title_tag else 'Без названия'

        # Краткое описание — берем alt из картинки (часто информативно)
        description = img_tag['alt'] if img_tag and img_tag.has_attr('alt') else ''
        # Если надо добавить рубрику к описанию:
        if rubric:
            description = f"[{rubric}] {description}"

        fe = fg.add_entry()
        fe.title(title)
        if link:
            fe.link(href=link)
        fe.pubDate(pub_date)
        if description:
            fe.description(description)
        if image:
            fe.enclosure(image, 0, 'image/jpeg')

    fg.rss_file('paper_is.xml')

if __name__ == '__main__':
    generate()

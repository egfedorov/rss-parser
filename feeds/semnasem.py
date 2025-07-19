import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

def parse_semnasem_date(date_str):
    # Пример: '18 июля, 9:43' или '10 июля'
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
        'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    now = datetime.now()
    try:
        # С временем (например, "18 июля, 9:43")
        m = re.match(r'(\d{1,2}) ([а-яё]+), (\d{1,2}):(\d{2})', date_str.strip())
        if m:
            day, month_str, hour, minute = m.groups()
            month = months[month_str.lower()]
            year = now.year
            dt = datetime(year, month, int(day), int(hour), int(minute), tzinfo=timezone.utc)
            # Если месяц "будущий" — материал за прошлый год
            if dt > datetime.now(timezone.utc):
                dt = dt.replace(year=year-1)
            return dt
        # Только день (например, "10 июля")
        m = re.match(r'(\d{1,2}) ([а-яё]+)', date_str.strip())
        if m:
            day, month_str = m.groups()
            month = months[month_str.lower()]
            year = now.year
            dt = datetime(year, month, int(day), 12, 0, tzinfo=timezone.utc)
            if dt > datetime.now(timezone.utc):
                dt = dt.replace(year=year-1)
            return dt
    except Exception:
        pass
    # fallback: сейчас
    print(f"❌ Не удалось распознать дату: {date_str}")
    return datetime.now(timezone.utc)

def generate():
    url = 'https://semnasem.org/tags/istorii'
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('7x7 — Истории')
    fg.link(href=url, rel='alternate')
    fg.description('Свежие материалы из раздела "Истории" на 7x7')
    fg.language('ru')

    for wrap in soup.select('.tag-materials-grid .material-teaser-wrap'):
        # Ссылка и картинка
        a_tag = wrap.select_one('a')
        if not a_tag:
            continue
        href = a_tag.get('href', '')
        if not href.startswith('http'):
            href = 'https://semnasem.org' + href
        img_div = a_tag.select_one('.material-teaser-illustration')
        image = ''
        if img_div and img_div.has_attr('style'):
            m = re.search(r"url\(['\"]?(.*?)['\"]?\)", img_div['style'])
            if m:
                image = m.group(1)
                if image.startswith('/'):
                    image = 'https://semnasem.org' + image

        # Дата
        date_tag = wrap.select_one('.material-teaser-date')
        date_str = date_tag.get_text(strip=True) if date_tag else ''
        pub_date = parse_semnasem_date(date_str)

        # Заголовок и описание
        title_tag = wrap.select_one('.material-teaser-title')
        title = title_tag.get_text(strip=True) if title_tag else 'Без названия'
        desc_tag = wrap.select_one('.material-teaser-body-content')
        description = desc_tag.get_text(strip=True) if desc_tag else ''

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=href)
        if description:
            fe.description(description)
        fe.pubDate(pub_date)
        if image:
            fe.enclosure(image, 0, 'image/jpeg')

    fg.rss_file('semnasem.xml')

if __name__ == '__main__':
    generate()

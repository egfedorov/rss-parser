import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

MONTHS = {
    'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'мая': 5, 'июн': 6,
    'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12
}

def parse_date(date_str: str) -> datetime:
    """
    Преобразует '17 июл 2025, 15:01' в datetime с UTC.
    """
    try:
        match = re.match(r"(\d{1,2}) (\w{3}) (\d{4}), (\d{2}):(\d{2})", date_str.strip())
        if match:
            day, mon, year, hour, minute = match.groups()
            month = MONTHS.get(mon.lower(), 1)
            return datetime(int(year), int(month), int(day), int(hour), int(minute), tzinfo=timezone.utc)
    except Exception:
        pass
    return datetime.now(timezone.utc)

def generate():
    url = 'https://sib.express/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Сиб.Экспресс — Главная')
    fg.link(href=url, rel='alternate')
    fg.description('Новости Сиб.Экспресс')
    fg.language('ru')

    # Блоки с новостями
    for announce in soup.select('.announce-3-in-line'):
        for div in announce.select('div'):
            a = div.find('a', class_='announce-3-in-line-block__link')
            if not a:
                continue
            link = a['href']
            if not link.startswith('http'):
                link = 'https://sib.express' + link
            title_tag = a.select_one('.announce-3-in-line-block__title p')
            title = title_tag.get_text(strip=True) if title_tag else None
            date_tag = a.select_one('.announce-3-in-line-block__date')
            date_str = date_tag.get_text(strip=True) if date_tag else ''
            pub_date = parse_date(date_str)
            image_tag = a.select_one('.announce-3-in-line-block__image')
            image_url = ''
            if image_tag and 'background-image' in image_tag.attrs.get('style', ''):
                style = image_tag['style']
                m = re.search(r'url\((.*?)\)', style)
                if m:
                    image_url = m.group(1)

            if not (title and link):
                continue

            fe = fg.add_entry()
            fe.id(link)  # Явно задаём guid!
            fe.title(title)
            fe.link(href=link)
            fe.pubDate(pub_date)
            if image_url:
                fe.enclosure(image_url, 0, 'image/jpeg')

    # Фото-пост, который идёт отдельным блоком
    photo_post = soup.select_one('.index-photo-post__link')
    if photo_post:
        link = photo_post['href']
        if not link.startswith('http'):
            link = 'https://sib.express' + link
        title_tag = photo_post.select_one('.index-photo-post__title')
        title = title_tag.get_text(strip=True) if title_tag else None
        # --- Дата для фото-поста ---
        date_tag = photo_post.select_one('.announce-3-in-line-block__date')
        date_str = date_tag.get_text(strip=True) if date_tag else ''
        pub_date = parse_date(date_str) if date_str else datetime.now(timezone.utc)
        # --- Картинка для фото-поста ---
        style = photo_post.attrs.get('style', '')
        m = re.search(r'url\(\'(.*?)\'\)', style)
        image_url = m.group(1) if m else ''

        if title and link:
            fe = fg.add_entry()
            fe.id(link)
            fe.title(title)
            fe.link(href=link)
            fe.pubDate(pub_date)
            if image_url:
                fe.enclosure(image_url, 0, 'image/jpeg')

    fg.rss_file('sibexpress.xml')

if __name__ == "__main__":
    generate()

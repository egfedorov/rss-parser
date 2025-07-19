import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

BASE = 'https://texty.org.ua'

def parse_date(date_str):
    # Пример: 2025-07-17 12:17
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})', date_str.strip())
    if m:
        year, month, day, hour, minute = map(int, m.groups())
        return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def generate():
    url = BASE + '/projects/'
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Texty.org.ua — Projects')
    fg.link(href=url, rel='alternate')
    fg.description('Головна стрічка проектів Texty.org.ua')
    fg.language('uk')

    for art in soup.select('article.pj'):
        # Ссылка
        a = art.find('a', href=True)
        href = a['href'] if a else ''
        if href and not href.startswith('http'):
            href = BASE + href

        # Заголовок
        title_tag = art.find('h3')
        title = title_tag.get_text(strip=True) if title_tag else 'Без назви'

        # Дата публикации
        time_tag = art.find('time', class_='published_at')
        date_str = time_tag.get_text(strip=True) if time_tag else ''
        pub_date = parse_date(date_str) if date_str else datetime.now(timezone.utc)

        # Описание (lead)
        lead_tag = art.find('div', class_='lead')
        description = lead_tag.get_text(strip=True) if lead_tag else title

        # Картинка (cover)
        img_div = art.find('div', class_='cover')
        image = ''
        if img_div and 'style' in img_div.attrs:
            m = re.search(r'url\([\'"]?([^\'")]+)[\'"]?\)', img_div['style'])
            if m:
                image = m.group(1)
                if image.startswith('/'):
                    image = BASE + image

        # Теги
        tags = []
        for tag_a in art.select('a.tag'):
            tag = tag_a.get_text(strip=True)
            if tag:
                tags.append({'term': tag})

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=href)
        fe.pubDate(pub_date)
        fe.description(description)
        if image:
            fe.enclosure(image, 0, 'image/jpeg')
        if tags:
            for tag_dict in tags:
                fe.category(tag_dict)

    fg.rss_file('texty.xml')

if __name__ == '__main__':
    generate()

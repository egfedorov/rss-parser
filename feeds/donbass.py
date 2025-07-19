import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

BASE = 'https://novosti.dn.ua'

def parse_date(date_str):
    # Пример: 18 июля 2025, 13:25
    months = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
              'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12}
    m = re.match(r'(\d{1,2}) (\w+) (\d{4}), (\d{2}):(\d{2})', date_str.strip())
    if m:
        day, month, year, hour, minute = m.groups()
        dt = datetime(int(year), months[month], int(day), int(hour), int(minute))
        # Сделать datetime aware (UTC)
        dt = dt.replace(tzinfo=timezone.utc)
        return dt
    # Если дата не распарсилась — текущая aware-UTC
    return datetime.now(timezone.utc)

def generate():
    url = BASE + '/ru/article'
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Новини Донбасу — Статьи')
    fg.link(href=url, rel='alternate')
    fg.description('Главная лента статей сайта novosti.dn.ua')
    fg.language('ru')

    for div in soup.select('.news'):
        # Ссылка
        a = div.find('a', class_='visual')
        if not a:
            continue
        href = a['href']
        if not href.startswith('http'):
            href = BASE + href

        # Заголовок
        title_tag = div.select_one('.news__title')
        title = title_tag.get_text(strip=True) if title_tag else a.get_text(strip=True)

        # Автор (иногда в первом .news__date)
        author = ''
        date_tag = div.select('div.news__date')
        if date_tag:
            # Первый news__date — автор (если есть), второй — дата
            if len(date_tag) > 1 and ',' not in date_tag[0].get_text():
                author = date_tag[0].get_text(strip=True)
                date_str = date_tag[1].get_text(strip=True)
            else:
                date_str = date_tag[0].get_text(strip=True)
        else:
            date_str = ''

        # Дата публикации (всегда aware)
        pub_date = parse_date(date_str) if date_str else datetime.now(timezone.utc)

        # Картинка
        img = ''
        img_tag = div.find('img', class_='bttrlazyloading')
        if img_tag:
            img = img_tag.get('src') or img_tag.get('data-bttrlazyloading-sm-src') or ''

        # Теги
        tags = []
        tags_ul = div.select_one('ul.news__tags')
        if tags_ul:
            tags = [li.get_text(strip=True) for li in tags_ul.find_all('a')]

        # Описание (можно добавить расширение: первую строку со страницы)
        description = title

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=href)
        fe.pubDate(pub_date)
        fe.description(description)
        if img:
            fe.enclosure(img, 0, 'image/jpeg')
        if tags:
           for tag in tags:
               fe.category({'term': tag})
        if author:
            fe.author({'name': author})

    fg.rss_file('donbass.xml')

if __name__ == '__main__':
    generate()

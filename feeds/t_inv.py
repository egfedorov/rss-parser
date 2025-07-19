import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

def parse_russian_date(date_str):
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    m = re.match(r'(\d{1,2}) ([а-яё]+) (\d{4})', date_str.strip())
    if m:
        day, month_str, year = m.groups()
        month = months[month_str]
        return datetime(int(year), month, int(day), 12, 0, tzinfo=timezone.utc)
    raise ValueError(f'Не удалось распарсить дату: {date_str}')

def get_pub_date(article_url):
    try:
        resp = requests.get(article_url, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        author_date_div = soup.select_one('.t-inv-post-author-and-date')
        if author_date_div:
            date_anchors = author_date_div.find_all('a')
            if date_anchors:
                date_text = date_anchors[-1].text.strip()
                return parse_russian_date(date_text)
        print(f"❌ Не удалось найти дату для {article_url}")
    except Exception as e:
        print(f"❌ Ошибка получения даты для {article_url}: {e}")
    return datetime.now(timezone.utc)

def generate():
    url = 'https://t-invariant.org/texts/'
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('T-invariant — Тексты')
    fg.link(href=url, rel='alternate')
    fg.description('Главная лента текстов T-invariant')
    fg.language('ru')

    for block in soup.select('.t-inv-block-posts'):
        for a in block.select('a[data-wpel-link]'):
            href = a['href']
            if not href.startswith('http'):
                href = 'https://t-invariant.org' + href

            # Заголовок
            title_tag = a.select_one('.t-inv-title')
            title = title_tag.get_text(strip=True) if title_tag else 'Без названия'

            # Лид (описание)
            lead_tag = a.select_one('.t-inv-lead')
            description = lead_tag.get_text(strip=True) if lead_tag else ''

            # Картинка (background-image)
            thumb_tag = a.select_one('.t-inv-thumb')
            image = ''
            if thumb_tag and 'style' in thumb_tag.attrs:
                m = re.search(r'background-image:\s*url\(([^)]+)\)', thumb_tag['style'])
                if m:
                    image = m.group(1)

            # Получаем дату публикации из самой статьи
            pub_date = get_pub_date(href)

            fe = fg.add_entry()
            fe.title(title)
            fe.link(href=href)
            fe.pubDate(pub_date)
            if description:
                fe.description(description)
            if image:
                fe.enclosure(image, 0, 'image/jpeg')

    fg.rss_file('t_inv.xml')

if __name__ == '__main__':
    generate()

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin
from datetime import datetime, timezone
import re

def parse_article_date(link, fallback_html=None):
    # Пробуем вытащить дату из ссылки: /2025/06/18/kryktytau
    m = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', link)
    if m:
        year, month, day = map(int, m.groups())
        return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
    # Если что — идём внутрь самой статьи (опционально)
    if fallback_html is not None:
        soup = BeautifulSoup(fallback_html, 'html.parser')
        # Например: <span class="date-display-single" ...>18.06.2025</span>
        date_tag = soup.find(class_=re.compile(r'date-display-single'))
        if date_tag:
            match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', date_tag.text)
            if match:
                day, month, year = map(int, match.groups())
                return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
    # Если совсем ничего нет
    return datetime.now(timezone.utc)

def generate():
    base_url = 'https://ovd.info'
    url = f'{base_url}/articles'
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('ОВД-Инфо — Статьи')
    fg.link(href=url, rel='alternate')
    fg.description('Все статьи с сайта ОВД-Инфо')
    fg.language('ru')

    # Парсим первые 20 статей с главной страницы /articles
    for card in soup.select('.views-row .media-anons-cont'):
        title_tag = card.select_one('.media-title')
        link_tag = title_tag if title_tag and title_tag.has_attr('href') else card.find('a', href=True)
        desc_tag = card.select_one('.media-text-more-media-text')
        title = title_tag.text.strip() if title_tag else None
        link = urljoin(base_url, link_tag['href']) if link_tag else None
        description = desc_tag.text.strip() if desc_tag else None

        if not (title and link):
            continue

        pub_date = parse_article_date(link)
        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        if description:
            fe.description(description)
        fe.pubDate(pub_date)

    fg.rss_file('ovd_texts.xml')

if __name__ == '__main__':
    generate()

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin
from datetime import datetime, timezone
import re

def parse_article_date(link):
    # Сначала пробуем вытащить дату из url вида /2025/06/18/kryktytau
    m = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', link)
    if m:
        year, month, day = map(int, m.groups())
        return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
    # Если не вышло — идём в саму статью и ищем <time datetime="...">
    try:
        resp = requests.get(link, timeout=7)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        time_tag = soup.find('time', attrs={'datetime': True})
        if time_tag and time_tag.has_attr('datetime'):
            dt_str = time_tag['datetime']
            # Попробуем iso-формат
            return datetime.fromisoformat(dt_str)
        # Fallback: .date-display-single 18.06.2025
        date_tag = soup.find(class_=re.compile(r'date-display-single'))
        if date_tag:
            match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', date_tag.text)
            if match:
                day, month, year = map(int, match.groups())
                return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
    except Exception as e:
        print(f"⚠️ Не удалось получить дату для {link}: {e}")
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

    # Корректный селектор к статьям!
    for card in soup.select('div.view-content > div.views-row'):
        a_tag = card.select_one('a.media-title')
        if not a_tag:
            continue
        link = a_tag['href']
        if not link.startswith('http'):
            link = urljoin(base_url, link)
        title = a_tag.get_text(strip=True)
        desc_tag = card.select_one('span.material-text-more-media-text')
        description = desc_tag.get_text(strip=True) if desc_tag else title

        pub_date = parse_article_date(link)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.pubDate(pub_date)

    fg.rss_file('ovd_texts.xml')

if __name__ == '__main__':
    generate()

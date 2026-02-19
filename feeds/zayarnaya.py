import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
    'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}

def parse_date(date_str: str) -> datetime:
    """
    '11 июля, 2025, 17:21' или '11 июля 2025, 17:21' => datetime(2025, 7, 11, 17, 21)
    """
    try:
        # Универсальная регулярка: допускает запятые/пробелы
        match = re.match(
            r"(\d{1,2})\s+([а-яА-ЯёЁ]+)[,]?\s*(\d{4})[,]?\s*(\d{1,2}):(\d{2})",
            date_str.strip()
        )
        if match:
            day = int(match.group(1))
            month = MONTHS[match.group(2).lower()]
            year = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    except Exception:
        print(f"[WARN] Не удалось распарсить дату: '{date_str}'")
    return datetime.now(timezone.utc)

def generate():
    return
    
    url = 'https://161.ru/text/author/170234/'
    response = requests.get(url)
    response.encoding = 'utf-8'  # Явно задаём
    soup = BeautifulSoup(response.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Алина Заярная')
    fg.link(href=url, rel='alternate')
    fg.description('Публикации автора на 161.ru')
    fg.language('ru')

    articles = soup.select('article.wrap_iDuIe')

    for art in articles:
        link_tag = art.select_one('a.imgBg_iDuIe')
        title_tag = art.select_one('a.header_iDuIe span')
        date_tag = art.select_one('.cell_eiDCU .text_eiDCU')

        title = title_tag.get_text(strip=True) if title_tag else None
        link = link_tag['href'] if link_tag and link_tag.has_attr('href') else None
        if link and not link.startswith('http'):
            link = 'https://161.ru' + link

        date_str = date_tag.get_text(strip=True) if date_tag else None
        pub_date = parse_date(date_str) if date_str else datetime.now()

        # Картинка (enclosure)
        img_tag = art.select_one('picture img')
        img_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None

        if not (title and link):
            continue

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pub_date)
        if img_url:
            fe.enclosure(img_url, 0, 'image/jpeg')

    fg.rss_file('zayarnaya.xml', encoding='utf-8')

if __name__ == '__main__':
    generate()

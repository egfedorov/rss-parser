import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
    'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

def parse_date(date_str: str) -> datetime:
    match = re.search(
        r"(\d{1,2})\s+([а-яё]+)[,]?\s*(\d{4})[,]?\s*(\d{2}):(\d{2})",
        date_str.lower()
    )
    if not match:
        raise ValueError(f"Не удалось распарсить дату: {date_str}")

    day, month_str, year, hour, minute = match.groups()
    return datetime(
        int(year),
        MONTHS[month_str],
        int(day),
        int(hour),
        int(minute),
        tzinfo=timezone.utc
    )

def generate():
    url = 'https://www.e1.ru/text/author/8531/'
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    articles = soup.select('article.wrap_iDuIe')
    if not articles:
        print("⚠️  Карточки статей не найдены")
        return

    fg = FeedGenerator()
    fg.id(url)
    fg.title('E1.ru — Елена Панкратьева')
    fg.link(href=url, rel='alternate')
    fg.description('Публикации автора на E1.ru')
    fg.language('ru')

    for art in articles:
        title_tag = art.select_one('a.header_iDuIe span')
        link_tag = art.select_one('a.header_iDuIe')
        date_tag = art.select_one('div.statistic_iDuIe span.text_eiDCU')

        if not (title_tag and link_tag and date_tag):
            continue

        title = title_tag.get_text(strip=True)
        link = link_tag['href']

        date_str = date_tag.get_text(strip=True)
        try:
            pub_date = parse_date(date_str)
        except Exception as e:
            print(f"[WARN] {e}")
            continue

        img_tag = art.select_one('picture img')
        img_url = img_tag['src'] if img_tag else None

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.published(pub_date)

        if img_url:
            fe.enclosure(img_url, 0, 'image/jpeg')

    fg.rss_file('pankratyeva.xml', encoding='utf-8')
    print("✅ RSS успешно сгенерирован")

if __name__ == '__main__':
    generate()

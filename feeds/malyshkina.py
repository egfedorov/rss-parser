import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re


URL = 'https://72.ru/text/author/159611/'
BASE = 'https://72.ru'

MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}

UA_DESKTOP = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/117.0.0.0 Safari/537.36'
    )
}

UA_MOBILE = {
    'User-Agent': (
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
        'AppleWebKit/605.1.15 (KHTML, like Gecko) '
        'Version/17.0 Mobile/15E148 Safari/604.1'
    )
}


# ----------------------
#  PARSE DATE
# ----------------------
def parse_date(s: str) -> datetime:
    m = re.search(
        r'(\d{1,2})\s+([а-яё]+),?\s*(\d{4}),?\s*(\d{1,2}):(\d{2})',
        s.lower()
    )
    if not m:
        raise ValueError(f'Не удалось распарсить дату: {s}')

    d, mon, y, h, mi = m.groups()
    return datetime(
        int(y),
        MONTHS[mon],
        int(d),
        int(h),
        int(mi),
        tzinfo=timezone.utc
    )


# ----------------------
#  FETCH + DIAG
# ----------------------
def fetch_html(headers):
    r = requests.get(URL, headers=headers, timeout=15)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')
    return r, soup


def diagnose(soup, label: str):
    articles = soup.find_all('article')
    ann = soup.select_one('[class*="announcementList"]')

    print(f'\n=== Диагностика: {label} ===')
    print(f'Найдено <article>: {len(articles)}')
    print(f'Есть ли announcementList: {bool(ann)}')
    print('================================\n')

    return len(articles)


# ----------------------
#  EXTRACT ARTICLES
# ----------------------
def extract_articles(soup):
    articles_data = []

    for art in soup.find_all('article'):
        title_tag = art.select_one('a[class*="header"] span')
        link_tag = art.find('a', href=True)
        date_tag = art.select_one('span[class*="text"]')

        if not (title_tag and link_tag and date_tag):
            continue

        title = title_tag.get_text(strip=True)

        link = link_tag['href']
        if link.startswith('/'):
            link = BASE + link

        try:
            pub_date = parse_date(date_tag.get_text(strip=True))
        except Exception as e:
            print(f'[WARN] {e}')
            continue

        img = None
        img_tag = art.select_one('picture img')
        if img_tag and img_tag.has_attr('src'):
            img = img_tag['src']

        articles_data.append({
            'title': title,
            'link': link,
            'date': pub_date,
            'img': img
        })

    return articles_data


# ----------------------
#  RSS BUILDER
# ----------------------
def build_rss(items):
    fg = FeedGenerator()

    fg.title('72.ru — Малышкина')
    fg.link(href=URL)
    fg.description('Публикации автора на 72.ru')
    fg.language('ru')

    for item in items:
        fe = fg.add_entry()
        fe.id(item['link'])
        fe.title(item['title'])
        fe.link(href=item['link'])
        fe.pubDate(item['date'])

        if item['img']:
            fe.enclosure(item['img'], 0, 'image/jpeg')

    # ВАЖНО: оставляем старое имя файла
    fg.rss_file('malyshkina.xml', encoding='utf-8')
    print('[OK] RSS создан: malyshkina.xml')


# ----------------------
#  MAIN
# ----------------------
def generate():

    # 1. Пробуем DESKTOP HTML
    r1, soup1 = fetch_html(UA_DESKTOP)
    print('Статус DESKTOP:', r1.status_code, 'Длина:', len(r1.text))
    desktop_count = diagnose(soup1, 'Десктопная версия')

    if desktop_count > 0:
        print('[INFO] Используем DESKTOP HTML')
        data = extract_articles(soup1)
        build_rss(data)
        return

    # 2. Если десктоп пуст — пробуем MOBILE HTML
    r2, soup2 = fetch_html(UA_MOBILE)
    print('Статус MOBILE:', r2.status_code, 'Длина:', len(r2.text))
    mobile_count = diagnose(soup2, 'Мобильная версия')

    if mobile_count == 0:
        print('[FATAL] Нет статей ни в одной версии HTML. Сайт отдаёт пустую разметку.')
        return

    print('[INFO] Используем MOBILE HTML')
    data = extract_articles(soup2)
    build_rss(data)


if __name__ == '__main__':
    generate()

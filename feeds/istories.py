import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin

def parse_date(date_str):
    # Пример: "15 июля"
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    parts = date_str.strip().split()
    if len(parts) == 2:
        day = int(parts[0])
        month = months.get(parts[1].lower(), 1)
        now = datetime.now()
        return datetime(now.year, month, day, tzinfo=timezone.utc)
    return datetime.now()

def generate():
    URL = 'https://istories.media/stories/'
    OUTPUT_FILE = 'feed_istories.xml'
    headers = {
        'User-Agent': 'Mozilla/5.0',
    }

    resp = requests.get(URL, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')

    cards = soup.select('div.MaterialCard-module--Wrapper--pMNOW')
    if not cards:
        print("⚠️ istories: статьи не найдены.")
        return

    fg = FeedGenerator()
    fg.title('Istories: Истории')
    fg.link(href=URL)
    fg.description('Публикации из раздела «Истории» на istories.media')

    for card in cards[:20]:
        title_el = card.select_one('div.MaterialCard-module--Header--vn88g a')
        summary_el = card.select_one('div.MaterialCard-module--Lead--gopri span')
        date_el = card.select_one('div.MaterialCard-module--DateContainer--FyTll')

        if not title_el:
            continue

        link = urljoin(URL, title_el['href'])
        title = title_el.get_text(strip=True)
        summary = summary_el.get_text(strip=True) if summary_el else ''
        pub_date = parse_date(date_el.get_text(strip=True)) if date_el else datetime.now(timezone.utc)
        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pub_date)
        fe.summary(summary)

    fg.rss_file(OUTPUT_FILE)
    print("✅ istories: сгенерирован feed_istories.xml")

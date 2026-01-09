import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin

def parse_date(date_str):
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    parts = date_str.strip().split()
    if len(parts) == 3:
        day = int(parts[0])
        month = months.get(parts[1].lower(), 1)
        year = int(parts[2])
        return datetime(year, month, day, tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def generate():
    BASE_URL = 'https://theins.ru'
    URL = f'{BASE_URL}/confession'
    OUTPUT_FILE = 'ins_confession.xml'
    headers = {'User-Agent': 'Mozilla/5.0'}

    resp = requests.get(URL, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')

    articles = soup.select('article._3ObqY')
    fg = FeedGenerator()
    fg.title('The Insider — Исповедь')
    fg.link(href=URL, rel='alternate')
    fg.description('RSS-лента с раздела "Исповедь" сайта The Insider')

    for art in articles:
        title_el = art.select_one('h3.D5w_o')
        link_el = art.select_one('a[href]')
        date_el = art.select_one('time._2nyD7')
        author_el = art.select_one('h5.xxhf')

        if not (title_el and link_el):
            continue

        title = title_el.get_text(strip=True)
        link = urljoin(BASE_URL, link_el['href'])
        author = author_el.get_text(strip=True) if author_el else 'Без автора'
        pub_date = parse_date(date_el.get_text(strip=True)) if date_el else datetime.now(timezone.utc)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.author({'name': author})
        fe.pubDate(pub_date)

    fg.rss_file(OUTPUT_FILE, pretty=True)
    print("✅ ins_confession: сгенерирован ins_confession.xml")

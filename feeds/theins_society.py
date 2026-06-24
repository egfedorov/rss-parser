import requests
import certifi
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
    # Формат: "13 июня 2026 г."
    parts = date_str.strip().rstrip('г.').strip().split()
    if len(parts) == 3:
        try:
            day = int(parts[0])
            month = months.get(parts[1].lower(), 1)
            year = int(parts[2])
            return datetime(year, month, day, tzinfo=timezone.utc)
        except (ValueError, IndexError):
            pass
    return datetime.now(timezone.utc)
    

def generate():
    BASE_URL = 'https://theins.ru'
    URL = f'{BASE_URL}/obshestvo'
    OUTPUT_FILE = 'feed_theins_society.xml'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    resp = requests.get(URL, headers=headers, verify=certifi.where())
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, 'html.parser')

    cards = soup.select('div[class*="articleList_cardWrapper"]')
    if not cards:
        print("⚠️ theins: статьи не найдены.")
        return

    articles = soup.select('article._3ObqY')
    fg = FeedGenerator()
    fg.title('The Insider — Общество')
    fg.link(href=URL, rel='alternate')
    fg.description('RSS-лента с раздела "Общество" сайта The Insider')

    seen_links = set()

    for card in cards:
        link_el = card.select_one('a[class*="articleCard_title"]')
        title_el = card.select_one('a[class*="articleCard_title"] h3')
        author_els = card.select('div[class*="articleCard_name"]')
        date_el = card.select_one('div[class*="articleCard_date"]')

        if not link_el or not title_el:
            continue

        link = urljoin(BASE_URL, link_el['href'])
        if link in seen_links:
            continue
        seen_links.add(link)

        title = title_el.get_text(strip=True)
        authors = [a.get_text(strip=True) for a in author_els if a.get_text(strip=True)]
        author = ', '.join(authors) if authors else 'The Insider'
        pub_date = parse_date(date_el.get_text(strip=True)) if date_el else datetime.now(timezone.utc)

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.author({'name': author})
        fe.pubDate(pub_date)

    fg.rss_file(OUTPUT_FILE, pretty=True)
    print("✅ theins_society: сгенерирован feed_theins_society.xml")


if __name__ == "__main__":
    generate()

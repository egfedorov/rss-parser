import requests
import certifi
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin


def generate():
    BASE_URL = 'https://mr-7.ru'
    URL = f'{BASE_URL}/stories'
    OUTPUT_FILE = 'mr7.xml'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    resp = requests.get(URL, headers=headers, verify=certifi.where())
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, 'html.parser')

    cards = soup.select('div.alCK3')
    if not cards:
        print("⚠️ mr7: статьи не найдены.")
        return

    fg = FeedGenerator()
    fg.title('МР7 — Истории')
    fg.link(href=URL, rel='alternate')
    fg.description('RSS-лента раздела «Истории» сайта mr-7.ru')
    fg.language('ru')

    seen_links = set()

    for card in cards:
        link_el = card.select_one('a.yrHoS')
        title_el = card.select_one('h2.ezXPQ b')
        author_els = card.select('a.BeDof')
        date_el = card.select_one('article-time')
        img_el = card.select_one('div.td8rx img')
        rubric_el = card.select_one('div.VmRZQ span')

        if not link_el or not title_el:
            continue

        link = urljoin(BASE_URL, link_el['href'])
        if link in seen_links:
            continue
        seen_links.add(link)

        title = title_el.get_text(strip=True)
        authors = [a.get_text(strip=True) for a in author_els if a.get_text(strip=True)]
        author = ', '.join(authors) if authors else 'МР7'
        img_url = urljoin(BASE_URL, img_el['src']) if img_el and img_el.get('src') else None

        # Дата из Unix timestamp в миллисекундах
        pub_date = datetime.now(timezone.utc)
        if date_el and date_el.get('date-time'):
            try:
                ts_ms = int(date_el['date-time'])
                pub_date = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
            except (ValueError, TypeError):
                pass

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.author({'name': author})
        fe.pubDate(pub_date)
        if img_url:
            fe.enclosure(img_url, 0, 'image/jpeg')

    fg.rss_file(OUTPUT_FILE, pretty=True)
    print(f"✅ mr7: сгенерирован mr7.xml ({len(seen_links)} статей)")


if __name__ == "__main__":
    generate()

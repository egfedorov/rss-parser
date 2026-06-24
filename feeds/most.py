import requests
import certifi
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin
import time


def fetch_pub_date(url, headers):
    try:
        resp = requests.get(url, headers=headers, verify=certifi.where(), timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        date_el = soup.select_one('span.date.post-date')
        if date_el:
            return datetime.strptime(date_el.get_text(strip=True), "%d/%m/%Y %H:%M").replace(tzinfo=timezone.utc)
    except Exception as e:
        print(f"⚠️ Не удалось получить дату для {url}: {e}")
    return datetime.now(timezone.utc)


def generate():
    BASE_URL = 'https://mostmedia.org'
    URL = f'{BASE_URL}/ru/latest-posts'
    OUTPUT_FILE = 'most.xml'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    resp = requests.get(URL, headers=headers, verify=certifi.where())
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, 'html.parser')

    container = soup.select_one('#postsblock')
    if not container:
        print("⚠️ mostmedia: контейнер #postsblock не найден.")
        return

    items = container.select('div[role="listitem"]')
    if not items:
        print("⚠️ mostmedia: статьи не найдены.")
        return

    fg = FeedGenerator()
    fg.title('Мост Медиа — последние публикации')
    fg.link(href=URL, rel='alternate')
    fg.description('RSS-лента последних публикаций сайта mostmedia.org')
    fg.language('ru')

    seen_links = set()

    for item in items:
        link_el = item.select_one('a.post-title')
        title_el = item.select_one('h3.h3')
        summary_el = item.select_one('div.intro-text')
        author_el = item.select_one('a.post-author')
        img_el = item.select_one('a.posts-image img')

        if not link_el or not title_el:
            continue

        link = urljoin(BASE_URL, link_el['href'])
        if link in seen_links:
            continue
        seen_links.add(link)

        title = title_el.get_text(strip=True)
        summary = summary_el.get_text(strip=True) if summary_el else ''
        author = author_el.get_text(strip=True) if author_el else 'Мост Медиа'
        img_url = urljoin(BASE_URL, img_el['src']) if img_el and img_el.get('src') else None

        # Заходим на страницу статьи за датой
        pub_date = fetch_pub_date(link, headers)
        time.sleep(0.5)  # небольшая пауза чтобы не перегружать сервер

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.summary(summary)
        fe.author({'name': author})
        fe.pubDate(pub_date)
        if img_url:
            fe.enclosure(img_url, 0, 'image/jpeg')

    fg.rss_file(OUTPUT_FILE, pretty=True)
    print(f"✅ mostmedia: сгенерирован most.xml ({len(seen_links)} статей)")


if __name__ == "__main__":
    generate()

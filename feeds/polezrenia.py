import requests
import certifi
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone


def parse_date(date_str):
    # Формат: "24.06.2026"
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def generate():
    URL = 'https://polezrenia.info/stories/'
    OUTPUT_FILE = 'polezrenia.xml'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    resp = requests.get(URL, headers=headers, verify=certifi.where())
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, 'html.parser')

    posts = soup.select('div.mzb-post')
    if not posts:
        print("⚠️ polezrenia: статьи не найдены.")
        return

    fg = FeedGenerator()
    fg.title('Поле зрения — Истории')
    fg.link(href=URL, rel='alternate')
    fg.description('RSS-лента раздела «Истории» сайта polezrenia.info')
    fg.language('ru')

    seen_links = set()

    for post in posts:
        link_el = post.select_one('h4.mzb-post-title a')
        date_el = post.select_one('span.mzb-post-date a')
        summary_el = post.select_one('div.mzb-entry-summary p')
        img_el = post.select_one('div.mzb-featured-image a img')

        if not link_el:
            continue

        link = link_el['href']
        if link in seen_links:
            continue
        seen_links.add(link)

        title = link_el.get_text(strip=True)
        summary = summary_el.get_text(strip=True) if summary_el else ''
        pub_date = parse_date(date_el.get_text(strip=True)) if date_el else datetime.now(timezone.utc)
        img_url = img_el['src'] if img_el else None

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.summary(summary)
        fe.pubDate(pub_date)
        if img_url:
            fe.enclosure(img_url, 0, 'image/jpeg')

    fg.rss_file(OUTPUT_FILE, pretty=True)
    print(f"✅ polezrenia: сгенерирован polezrenia.xml ({len(seen_links)} статей)")


if __name__ == "__main__":
    generate()

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def generate():
    BASE_URL = 'https://mostmedia.org'
    URL = f'{BASE_URL}/ru/latest-posts'
    OUTPUT_FILE = 'most.xml'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800},
            locale='ru-RU',
        )

        # Загружаем список статей
        page = context.new_page()
        stealth_sync(page)
        page.goto(URL, wait_until='networkidle', timeout=30000)
        html = page.content()

        if 'postsblock' not in html:
            print("⚠️ mostmedia: postsblock не найден.")
            browser.close()
            return

        soup = BeautifulSoup(html, 'html.parser')
        container = soup.select_one('#postsblock')
        items = container.select('div[role="listitem"]') if container else []

        if not items:
            print("⚠️ mostmedia: статьи не найдены.")
            browser.close()
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

            # Открываем страницу статьи через playwright
            pub_date = datetime.now(timezone.utc)
            try:
                article_page = context.new_page()
                stealth_sync(article_page)
                article_page.goto(link, wait_until='networkidle', timeout=20000)
                article_html = article_page.content()
                article_page.close()

                article_soup = BeautifulSoup(article_html, 'html.parser')
                date_el = article_soup.select_one('span.date.post-date')
                if date_el:
                    print(f"  Дата: {date_el.get_text(strip=True)} — {title[:40]}")
                    pub_date = datetime.strptime(date_el.get_text(strip=True), "%d/%m/%Y %H:%M").replace(tzinfo=timezone.utc)
                else:
                    print(f"  ⚠️ Дата не найдена: {title[:40]}")
            except Exception as e:
                print(f"  ⚠️ Ошибка загрузки статьи {link}: {e}")

            time.sleep(0.5)

            fe = fg.add_entry()
            fe.id(link)
            fe.title(title)
            fe.link(href=link)
            fe.summary(summary)
            fe.author({'name': author})
            fe.pubDate(pub_date)
            if img_url:
                fe.enclosure(img_url, 0, 'image/jpeg')

        browser.close()

    fg.rss_file(OUTPUT_FILE, pretty=True)
    print(f"✅ mostmedia: сгенерирован most.xml ({len(seen_links)} статей)")


if __name__ == "__main__":
    generate()

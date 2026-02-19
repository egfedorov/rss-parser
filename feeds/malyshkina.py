import os
import re
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

BASE = "https://72.ru"
MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}

def parse_date(s):
    try:
        m = re.search(r'(\d{1,2})\s+([а-яё]+)(?:,?\s*(\d{4}))?,?\s*(\d{1,2}):(\d{2})', s.lower())
        if not m:
            return datetime.now(timezone.utc)
        d, mon, y, h, mi = m.groups()
        year = int(y) if y else datetime.now(timezone.utc).year
        return datetime(year, MONTHS[mon], int(d), int(h), int(mi), tzinfo=timezone.utc)
    except:
        return datetime.now(timezone.utc)

def generate():
    return
    
    url = "https://72.ru/text/author/159611/"
    
    with sync_playwright() as p:
        print(f"[INFO] Запуск Playwright для {url}")
        # Запускаем браузер
        browser = p.chromium.launch(headless=True)
        # Эмулируем обычный Chrome на Windows
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        try:
            # Переходим и ждем, пока сетевая активность утихнет
            page.goto(url, wait_until="networkidle", timeout=60000)
            # Дополнительно ждем появления хотя бы одной статьи
            page.wait_for_selector("article", timeout=10000)
            html = page.content()
            print(f"[INFO] Страница успешно загружена ({len(html)} симв.)")
        except Exception as e:
            print(f"[ERROR] Ошибка Playwright: {e}")
            browser.close()
            return
        
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    articles = soup.find_all("article")
    print(f"[INFO] Найдено статей: {len(articles)}")

    if not articles:
        return

    fg = FeedGenerator()
    fg.title("72.ru — Малышкина")
    fg.link(href=url, rel="alternate")
    fg.description("Публикации автора на 72.ru")

    for art in articles:
        title_tag = art.find("h2") or art.select_one('a[class*="header"]')
        link_tag = art.find("a", href=True)
        date_tag = art.select_one('time') or art.select_one('span[class*="text"]')

        if not (title_tag and link_tag):
            continue

        title = title_tag.get_text(strip=True)
        link = urljoin(BASE, link_tag["href"])
        pubdate = parse_date(date_tag.get_text(strip=True)) if date_tag else datetime.now(timezone.utc)

        img_tag = art.find("img")
        img = img_tag.get("src") if img_tag else None

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pubdate)
        if img:
            fe.enclosure(img, 0, "image/jpeg")

    fg.rss_file("malyshkina.xml", pretty=True)
    print("[OK] RSS malyshkina.xml обновлен")

if __name__ == "__main__":
    generate()

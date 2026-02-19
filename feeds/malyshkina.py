import cloudscraper
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import time
import re
from urllib.parse import urljoin

BASE = "https://72.ru"

MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}

def parse_date(s):
    # Пытаемся найти: Число Месяц Год (опционально) Часы:Минуты
    # Например: "19 февраля 2026, 18:30" или "19 февраля, 18:30"
    try:
        m = re.search(r'(\d{1,2})\s+([а-яё]+)(?:,?\s*(\d{4}))?,?\s*(\d{1,2}):(\d{2})', s.lower())
        if not m:
            return datetime.now(timezone.utc)
            
        d, mon, y, h, mi = m.groups()
        
        # Если год не указан, берем текущий
        year = int(y) if y else datetime.now().year
        return datetime(year, MONTHS[mon], int(d), int(h), int(mi), tzinfo=timezone.utc)
    except Exception as e:
        print(f"[WARN] Ошибка парсинга даты '{s}': {e}")
        return datetime.now(timezone.utc)

def generate():
    # Создаем скрейпер
    scraper = cloudscraper.create_scraper()
    
    # Кэш-бастер
    ts = int(time.time() * 1000)
    url = f"https://72.ru/text/author/159611/?_dc={ts}"

    print(f"[INFO] Загружаем через cloudscraper: {url}")

    try:
        # Cloudscraper сам подставит правильные заголовки
        r = scraper.get(url, timeout=20)
        r.encoding = "utf-8"
        
        if r.status_code != 200:
            print(f"[ERROR] Не удалось пробить защиту. Статус: {r.status_code}")
            return
            
    except Exception as e:
        print(f"[FATAL] Ошибка запроса: {e}")
        return

    soup = BeautifulSoup(r.text, "html.parser")
    # На 72.ru статьи лежат в блоках с атрибутом data-testid="card-container" или просто в <article>
    articles = soup.find_all("article")

    print("[INFO] Найдено статей на странице:", len(articles))

    if not articles:
        print("[FATAL] Статьи не найдены. Возможно, изменилась структура DOM.")
        return

    fg = FeedGenerator()
    fg.title("72.ru — Малышкина")
    fg.link(href="https://72.ru/text/author/159611/", rel="alternate")
    fg.description("Публикации автора на 72.ru")
    fg.language("ru")

    for art in articles:
        # Названия классов на 72.ru часто содержат хеши, поэтому ищем по вхождению
        title_tag = art.find("h2") or art.select_one('a[class*="header"]')
        link_tag = art.find("a", href=True)
        # Дата обычно в span, который содержит текст с временем
        date_tag = art.select_one('time') or art.select_one('span[class*="text"]')

        if not (title_tag and link_tag):
            continue

        title = title_tag.get_text(strip=True)
        link = urljoin(BASE, link_tag["href"])
        
        # Извлекаем дату
        date_text = date_tag.get_text(strip=True) if date_tag else ""
        pubdate = parse_date(date_text)

        # Картинка
        img_tag = art.find("img")
        img = img_tag.get("src") if img_tag else None

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pubdate)
        if img:
            fe.enclosure(img, 0, "image/jpeg")
            
        print(f"✅ Обработано: {title[:40]}...")

    fg.rss_file("malyshkina.xml", pretty=True)
    print("[OK] RSS-фид malyshkina.xml успешно создан")

if __name__ == "__main__":
    generate()

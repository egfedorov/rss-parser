import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

BASE = 'https://www.kavkazr.com'
START_URL = BASE + '/p/7647.html'

def get_article_date(article_url):
    try:
        resp = requests.get(article_url, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Универсальный поиск даты публикации
        time_tag = soup.select_one("#content time[datetime]")
        if time_tag and time_tag.has_attr('datetime'):
            dt_str = time_tag['datetime']
            # datetime.fromisoformat требует +00:00 вместо Z
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except Exception as e:
        print(f"Ошибка при получении даты из {article_url}: {e}")
    return datetime.now(timezone.utc)

def is_valid_article(href, title):
    # Не добавлять мобильное приложение и другие мусорные ссылки
    if '/mobileapp' in href or 'мобильное приложение' in title.lower():
        return False
    # Можно добавить и другие фильтры по необходимости
    return True

def generate():
    r = requests.get(START_URL)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Кавказ.Реалии — Общество')
    fg.link(href=START_URL, rel='alternate')
    fg.description('Главная лента раздела "Общество" сайта kavkazr.com')
    fg.language('ru')

    # Собираем все статьи из ленты (основной и боковой колонки)
    seen_links = set()
    for li in soup.select('li'):
        a = li.select_one('a[href*="/a/"]')
        if not a:
            continue
        href = a['href']
        if not href.startswith('http'):
            href = BASE + href

        # Заголовок
        title_tag = li.select_one('h4')
        title = title_tag.get_text(strip=True) if title_tag else a.get('title', a.get_text(strip=True))

        # --- ФИЛЬТРАЦИЯ НЕСТАТЕЙ ---
        if not is_valid_article(href, title):
            continue

        if href in seen_links:
            continue
        seen_links.add(href)

        # Картинка (ищем <img> внутри .thumb)
        img = ''
        img_tag = li.select_one('img')
        if img_tag:
            img = img_tag.get('src') or img_tag.get('data-src') or ''

        # Получаем дату публикации (с таймзоной!)
        pub_date = get_article_date(href)

        # Описание
        description = title

        # Добавляем в RSS
        fe = fg.add_entry()
        fe.id(href)  # <--- Явно задаём guid!
        fe.title(title)
        fe.link(href=href)
        fe.pubDate(pub_date)
        fe.description(description)
        if img:
            fe.enclosure(img, 0, 'image/jpeg')

    fg.rss_file('kavkaz_soc.xml')

if __name__ == '__main__':
    generate()

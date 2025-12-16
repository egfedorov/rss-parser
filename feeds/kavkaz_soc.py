import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

BASE = 'https://www.kavkazr.com'
START_URL = BASE + '/p/7647.html'

# Все "плохие" ссылки или паттерны, которые нужно исключить из ленты
EXCLUDE_URLS = {
    f'{BASE}/a/28482722.html',  # "Новостное приложение" и подобные служебные ссылки
}
EXCLUDE_PATTERNS = [
    '/a/28482722',  # Явно баннер
    '/p/',          # Главные страницы и рубрики, не материалы
    '/apps',        # Приложения, мобильные баннеры
    '/about',       # Служебные страницы
    '/subscribe',
    '/info',
    '/mobileapps'
]

def should_exclude(href):
    if href in EXCLUDE_URLS:
        return True
    for pattern in EXCLUDE_PATTERNS:
        if pattern in href:
            return True
    return False

def get_article_date(article_url):
    try:
        resp = requests.get(article_url, timeout=(3, 5))
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        time_tag = soup.select_one("#content time[datetime]")
        if time_tag and time_tag.has_attr('datetime'):
            dt_str = time_tag['datetime']
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except Exception as e:
        print(f"Ошибка при получении даты из {article_url}: {e}")
    return datetime.now(timezone.utc)

def generate():
    r = requests.get(START_URL)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Кавказ.Реалии — Общество')
    fg.link(href=START_URL, rel='alternate')
    fg.description('Главная лента раздела "Общество" сайта kavkazr.com')
    fg.language('ru')

    seen_links = set()
    for li in soup.select('li'):
        a = li.select_one('a[href*="/a/"]')
        if not a:
            continue
        href = a['href']
        if not href.startswith('http'):
            href = BASE + href
        if href in seen_links:
            continue
        if should_exclude(href):
            continue
        seen_links.add(href)

        title_tag = li.select_one('h4')
        title = title_tag.get_text(strip=True) if title_tag else a.get('title', a.get_text(strip=True))

        img = ''
        img_tag = li.select_one('img')
        if img_tag:
            img = img_tag.get('src') or img_tag.get('data-src') or ''

        pub_date = get_article_date(href)
        description = title

        fe = fg.add_entry()
        fe.id(href)
        fe.title(title)
        fe.link(href=href)
        fe.pubDate(pub_date)
        fe.description(description)
        if img:
            fe.enclosure(img, 0, 'image/jpeg')

    fg.rss_file('kavkaz_soc.xml')

if __name__ == '__main__':
    generate()

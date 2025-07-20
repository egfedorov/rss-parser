import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin
from datetime import datetime, timezone
import re

EXCLUDE_PATTERNS = [
    '/about', '/archive', '/donate', '/login', '/register', '/search', '/static', '.pdf', 'facebook.com', 'twitter.com'
]

def should_exclude(link):
    for pat in EXCLUDE_PATTERNS:
        if pat in link:
            return True
    return False

def parse_date_from_report(url):
    try:
        resp = requests.get(url, timeout=7)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Типовая дата: <div class="instruction-header-meta"><span>18.12.2023</span></div>
        date_el = soup.select_one('.instruction-header-meta span')
        if date_el:
            date_str = date_el.get_text(strip=True)
            pub_date = datetime.strptime(date_str, "%d.%m.%Y").replace(tzinfo=timezone.utc)
            return pub_date
        # Если формат другой — <time datetime=...>
        time_el = soup.find('time', attrs={'datetime': True})
        if time_el:
            return datetime.fromisoformat(time_el['datetime'])
    except Exception as e:
        print(f"⚠️ Не удалось получить дату для {url}: {e}")
    return None

def guess_date_from_url(url):
    m = re.search(r'/(\d{4})/(\d{2})/(\d{2})', url)
    if m:
        year, month, day = map(int, m.groups())
        return datetime(year, month, day, tzinfo=timezone.utc)
    return None

def generate():
    base_url = 'https://reports.ovd.info'
    response = requests.get(base_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('ОВД-Инфо — Отчёты')
    fg.link(href=base_url, rel='alternate')
    fg.description('Обзоры, исследования и отчёты с сайта reports.ovd.info')
    fg.language('ru')

    seen_links = set()
    for card in soup.select('.legal-items a.legal-content'):
        href = card.get('href')
        if not href:
            continue
        link = urljoin(base_url, href)
        # Пропуск сервисных ссылок и уже добавленных
        if should_exclude(link) or link in seen_links:
            continue
        seen_links.add(link)

        # Title
        title_tag = card.select_one('.legal-details .title')
        title = title_tag.text.strip() if title_tag else 'Без названия'
        # Description (не всегда заполнено)
        desc_tag = card.select_one('.legal-details .description')
        description = desc_tag.text.strip() if desc_tag else None

        # Дата публикации — приоритет: из самой публикации > из url > пропуск
        pub_date = parse_date_from_report(link)
        if not pub_date:
            pub_date = guess_date_from_url(link)
        if not pub_date:
            print(f"❌ Не удалось определить дату для {link}, пропускаю...")
            continue

        fe = fg.add_entry()
        fe.id(link)  # guid — ссылка на материал
        fe.title(title)
        fe.link(href=link)
        if description:
            fe.description(description)
        fe.pubDate(pub_date)

    fg.rss_file('ovd_reports.xml')

if __name__ == '__main__':
    generate()

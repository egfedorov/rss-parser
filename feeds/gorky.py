import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

def parse_date_gorky(date_str):
    # Ожидаем вид: "18.07.2025"
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def generate():
    url = 'https://gorky.media/context'
    r = requests.get(url)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Горький — Контекст')
    fg.link(href=url, rel='alternate')
    fg.description('Раздел «Контекст» журнала Горький')
    fg.language('ru')

    for card in soup.select('a.border.block.p-6'):
        # Ссылка
        href = card.get('href')
        abs_url = href if href.startswith('http') else 'https://gorky.media' + href

        # Дата и автор
        date_author_div = card.select_one('.flex.items-center.mb-4')
        if date_author_div:
            ps = date_author_div.find_all('p')
            date_str = ps[0].get_text(strip=True) if ps else ''
            author = ps[2].get_text(strip=True) if len(ps) > 2 else ''
        else:
            date_str, author = '', ''

        # Заголовок
        title_tag = card.select_one('h2')
        title = title_tag.get_text(strip=True) if title_tag else 'Без названия'

        # Подзаголовок/анонс
        subtitle_tag = card.select_one('p.text-xl.italic')
        subtitle = subtitle_tag.get_text(strip=True) if subtitle_tag else ''

        # Краткое описание (первый абзац)
        desc_tag = card.select_one('p:not(.text-xl):not(.mb-2)')
        if desc_tag:
            desc = desc_tag.get_text(strip=True)
        else:
            desc = ''

        # Итоговое описание
        description = (subtitle + '\n\n' + desc).strip()

        # Дата
        pub_date = parse_date_gorky(date_str)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=abs_url)
        fe.author({'name': author})
        if description:
            fe.description(description)
        fe.pubDate(pub_date)

    fg.rss_file('gorky.xml')

if __name__ == '__main__':
    generate()

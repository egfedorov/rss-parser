import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
    'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}

def parse_date(date_str: str) -> datetime:
    match = re.match(r"(\d{1,2}) (\w+) (\d{4})", date_str.strip())
    if match:
        day = int(match.group(1))
        month = MONTHS.get(match.group(2).lower(), 1)
        year = int(match.group(3))
        return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def generate():
    url = 'https://regaspect.info/articles/'
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Регаспект — Статьи')
    fg.link(href=url, rel='alternate')
    fg.description('Все статьи с сайта regaspect.info')
    fg.language('ru')

    articles = soup.select('article.uagb-post__inner-wrap')

    for art in articles:
        title_tag = art.select_one('h3.uagb-post__title a')
        title = title_tag.text.strip() if title_tag else None
        link = title_tag['href'] if title_tag else None

        desc_tag = art.select_one('.uagb-post__excerpt')
        description = desc_tag.text.strip() if desc_tag else None

        date_tag = art.select_one('.uagb-post__date')
        if date_tag:
            date_str = date_tag.text.strip()
        else:
            date_str = None
            desc_and_html = art.get_text()
            match = re.search(r'(\d{1,2}) (\w+) (\d{4})', desc_and_html)
            if match:
                date_str = match.group(0)

        if not date_str and link:
            m = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', link)
            if m:
                year, month, day = map(int, m.groups())
                date_str = f"{day} {list(MONTHS.keys())[month-1]} {year}"

        if not title or not date_str or not link:
            continue

        pub_date = parse_date(date_str)
        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pub_date)
        if description:
            fe.description(description)

    fg.rss_file('regaspect.xml')

if __name__ == '__main__':
    generate()

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin
from datetime import datetime, timezone

def parse_date(text):
    # Пример: 10.07.2025, 02:33
    try:
        dt = datetime.strptime(text.split(',')[0], "%d.%m.%Y")
        # Можно пробовать вытаскивать и время, если нужно
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def generate():
    url = 'https://www.kommersant.ru/authors/51'
    base_url = 'https://www.kommersant.ru'

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Ольга Алленова — Коммерсантъ')
    fg.link(href=url, rel='alternate')
    fg.description('Лента материалов на kommersant.ru')
    fg.language('ru')

    for art in soup.select('article.rubric_lenta__item'):
        title = art.get('data-article-title') or art.select_one('h2.uho__name').text.strip()
        url_rel = art.get('data-article-url') or art.select_one('a.uho__link').get('href')
        url_abs = url_rel if url_rel.startswith('http') else urljoin(base_url, url_rel)
        date = art.select_one('.uho__tag').text.strip()
        desc = art.get('data-article-description', '')
        image = art.get('data-article-image', '')
        pub_date = parse_date(date)
        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=url_abs)
        if desc:
            fe.description(desc)
        fe.pubDate(pub_date)
        if image:
            fe.enclosure(image, 0, 'image/jpeg')

    fg.rss_file('allenova.xml')

if __name__ == '__main__':
    generate()

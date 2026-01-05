import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin

BASE_URL = 'https://72.ru'
AUTHOR_URL = 'https://72.ru/text/author/159611/'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; RSSBot/1.0)'
}

def get_pub_date(article_url: str) -> datetime:
    """
    Забираем дату со страницы статьи:
    <time datetime="2025-01-03T14:25:00+05:00">
    """
    try:
        r = requests.get(article_url, headers=HEADERS, timeout=15)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        time_tag = soup.find('time', attrs={'datetime': True})
        if time_tag:
            return datetime.fromisoformat(
                time_tag['datetime']
            ).astimezone(timezone.utc)

    except Exception as e:
        print(f'[WARN] Не удалось получить дату {article_url}: {e}')

    return datetime.now(timezone.utc)


def generate():
    r = requests.get(AUTHOR_URL, headers=HEADERS, timeout=15)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('72.ru — публикации автора')
    fg.link(href=AUTHOR_URL, rel='alternate')
    fg.description('Публикации автора на 72.ru')
    fg.language('ru')

    articles = soup.find_all('article')

    print(f'[INFO] Найдено статей: {len(articles)}')

    for art in articles:
        link_tag = art.find('a', href=True)
        title_tag = art.find('h2')

        if not link_tag or not title_tag:
            continue

        link = urljoin(BASE_URL, link_tag['href'])
        title = title_tag.get_text(strip=True)

        pub_date = get_pub_date(link)

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pub_date)

    fg.rss_file('malyshkina.xml', encoding='utf-8')
    print('[OK] RSS создан: malyshkina.xml')


if __name__ == '__main__':
    generate()

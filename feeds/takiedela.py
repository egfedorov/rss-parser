import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re
from dateutil import parser as dateparser

def generate():
    url = 'https://takiedela.ru/stories/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Такие дела — Истории')
    fg.link(href=url, rel='alternate')
    fg.description('Материалы из раздела «Истории» сайта takiedela.ru')
    fg.language('ru')

    articles = soup.select('ul.b-col-list li.b-col')

    for item in articles:
        title_tag = item.select_one('.b-material__head')
        link_tag = item.select_one('a.b-material__txt')
        description_tag = item.select_one('.b-material__lead')

        if not (title_tag and link_tag and description_tag):
            continue

        title = title_tag.get_text(strip=True)
        link = link_tag['href']
        description = description_tag.get_text(strip=True)

        pub_date = None

        # 1. Пытаемся получить дату публикации из самой статьи (<time datetime=...>)
        try:
            article_response = requests.get(link, timeout=5)
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            time_tag = article_soup.select_one('time[datetime]')
            if time_tag and time_tag.has_attr('datetime'):
                parsed = dateparser.parse(time_tag['datetime'])
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                pub_date = parsed.astimezone(timezone.utc)
        except Exception as e:
            print(f"⚠️ Не удалось получить дату из {link}: {e}")

        # 2. Если не нашли дату в статье — пробуем взять её из url (год/месяц)
        if not pub_date:
            date_match = re.search(r'/(\d{4})/(\d{2})/', link)
            if date_match:
                year, month = map(int, date_match.groups())
                pub_date = datetime(year, month, 1, tzinfo=timezone.utc)
            else:
                pub_date = datetime.now(timezone.utc)  # fallback

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.pubDate(pub_date)

    fg.rss_file('takiedela.xml')

if __name__ == '__main__':
    generate()

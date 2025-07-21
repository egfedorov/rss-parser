import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re
from dateutil import parser as dateparser
from urllib.parse import urljoin

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
        link = urljoin(url, link_tag['href'])
        description = description_tag.get_text(strip=True)

        pub_date = None

        # Открываем статью и ищем дату по строгому селектору
        try:
            article_response = requests.get(link, timeout=5)
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            # Жёстко: time внутри article > div:nth-child(1) > div > time
            # Иногда встречаются небольшие различия, поэтому можно взять просто:
            # article > div > div > time
            time_tag = article_soup.select_one('article > div > div > time')
            if time_tag and time_tag.has_attr('datetime'):
                parsed = dateparser.parse(time_tag['datetime'])
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                pub_date = parsed.astimezone(timezone.utc)
            else:
                print(f"‼️ Не найден <time> для {link}")
        except Exception as e:
            print(f"⚠️ Не удалось получить дату из {link}: {e}")

        # Если не нашли дату — пропускаем материал
        if not pub_date:
            print(f"‼️ Не удалось определить дату для {link}, пропускаем")
            continue

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.pubDate(pub_date)

    fg.rss_file('takiedela.xml')

if __name__ == '__main__':
    generate()

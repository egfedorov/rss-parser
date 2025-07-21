import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin
from datetime import datetime, timezone
import re

def parse_article_date(article_url):
    response = requests.get(article_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    # 1. <time> с датой
    time_tag = soup.find('time')
    if time_tag and time_tag.has_attr('datetime'):
        try:
            return datetime.fromisoformat(time_tag['datetime']).astimezone(timezone.utc)
        except Exception:
            pass
    # 2. Просто текст вида "15 июля 2024"
    text = ''
    for el in soup.find_all(string=re.compile(r'\d{1,2}\s+\w+\s+\d{4}')):
        text = el.strip()
        break
    if text:
        MONTHS = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
            'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
        }
        match = re.search(r'(\d{1,2}) (\w+) (\d{4})', text)
        if match:
            day = int(match.group(1))
            month = MONTHS.get(match.group(2).lower(), 1)
            year = int(match.group(3))
            return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def generate():
    url = 'https://www.currenttime.tv/longreads'
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    fg = FeedGenerator()
    fg.title('Настоящее Время — Лонгриды')
    fg.link(href=url, rel='alternate')
    fg.description('Лонгриды на сайте Настоящее Время')
    fg.language('ru')

    # Найти <div class="row"><ul>...</ul></div>
    news_list = soup.select_one('div.row ul')
    if not news_list:
        print('❌ Не найден основной блок с материалами!')
        return

    for li in news_list.select('li.fui-bob-grid'):
        link_tag = li.select_one('a.img-wrap')
        title_tag = li.select_one('h4.media-block__title')

        if not link_tag or not title_tag:
            continue

        link = urljoin(url, link_tag['href'])
        title = title_tag.text.strip()
        
        # Описание — опционально
        desc = title_tag['title'] if title_tag.has_attr('title') else ''
        # Картинка — опционально
        img_tag = li.select_one('img.enhanced')
        image = img_tag['src'] if img_tag and img_tag.has_attr('src') else None

        pub_date = parse_article_date(link)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pub_date)
        if desc:
            fe.description(desc)
        if image:
            fe.enclosure(image, 0, 'image/jpeg')

    fg.rss_file('current_time.xml')

if __name__ == '__main__':
    generate()

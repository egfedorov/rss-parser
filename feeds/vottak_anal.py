from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin
import re
import time

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
    url = 'https://vot-tak.tv/80933789/analitika'

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Даем странице полностью прогрузиться
    time.sleep(5)

    html = driver.page_source

    with open("vot_tak_selenium.html", "w", encoding="utf-8") as f:
        f.write(html)

    soup = BeautifulSoup(html, 'html.parser')
    driver.quit()

    fg = FeedGenerator()
    fg.title('Вот Так — Анализ')
    fg.link(href=url, rel='alternate')
    fg.description('Все истории с сайта vot-tak.tv')
    fg.language('ru')

    cards = soup.select('section.module-7-boxes a.bbb-box, section.module-7-boxes a.mb-box')

    for card in cards:
        title_tag = card.select_one('.bbb-box__title span') or card.select_one('.mb-box__title')
        title = title_tag.text.strip() if title_tag else None

        date_tag = card.select_one('.bbb-box__date') or card.select_one('.mb-box__date')
        date_str = date_tag.text.strip() if date_tag else None

        link = urljoin(url, card['href'])


        if not title or not date_str:
            continue

        pub_date = parse_date(date_str)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.pubDate(pub_date)

    fg.rss_file('vottak_anal.xml')

if __name__ == '__main__':
    generate()

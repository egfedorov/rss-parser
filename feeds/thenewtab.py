from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import time

def parse_russian_date(date_str):
    # "17 июля 2025"
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
        'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    parts = date_str.strip().split()
    if len(parts) == 3:
        day = int(parts[0])
        month = months.get(parts[1].lower(), 1)
        year = int(parts[2])
        return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def generate():
    url = "https://thenewtab.io/articles/"

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(4)  # Дать странице подгрузиться JS

    # Можно раскомментировать, чтобы проскроллить вниз и догрузить больше статей:
    # last_height = driver.execute_script("return document.body.scrollHeight")
    # for _ in range(3):  # сколько раз прокручивать (можно увеличить)
    #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #     time.sleep(2)
    #     new_height = driver.execute_script("return document.body.scrollHeight")
    #     if new_height == last_height:
    #         break
    #     last_height = new_height

    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, "html.parser")

    fg = FeedGenerator()
    fg.title("The New Tab — Статьи")
    fg.link(href=url, rel="alternate")
    fg.description("Материалы с сайта thenewtab.io")
    fg.language('ru')

    articles = soup.find_all("article")
    print(f"Найдено статей: {len(articles)}")
    for article in articles:
        title_tag = article.select_one(".entry_title a")
        summary_tag = article.select_one(".entry_subheader a")
        date_tag = article.select_one(".entry_date")

        if not title_tag or not date_tag:
            continue

        link = title_tag["href"]
        if not link.startswith("http"):
            link = "https://thenewtab.io" + link

        title = title_tag.get_text(strip=True)
        summary = summary_tag.get_text(strip=True) if summary_tag else ""
        date_str = date_tag.get_text(strip=True)
        pub_date = parse_russian_date(date_str)

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.description(summary)
        fe.pubDate(pub_date)

    fg.rss_file("thenewtab.xml")

if __name__ == "__main__":
    generate()

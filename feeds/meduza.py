from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re
import time

BASE_URL = "https://meduza.io"

def extract_date_from_url(url):
    match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
    if match:
        year, month, day = map(int, match.groups())
        return datetime(year, month, day, tzinfo=timezone.utc)
    return None

def scroll_until_loaded(driver, min_articles=60, max_scrolls=10):
    last_count = 0
    for _ in range(max_scrolls):
        articles = driver.find_elements(By.CSS_SELECTOR, ".RichBlock-module-title")
        if len(articles) >= min_articles:
            break
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4)
        new_count = len(driver.find_elements(By.CSS_SELECTOR, ".RichBlock-module-title"))
        if new_count == last_count:
            break
        last_count = new_count
    return driver.find_elements(By.CSS_SELECTOR, ".RichBlock-module-title")

def generate():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)

    url = f"{BASE_URL}/articles"
    driver.get(url)
    time.sleep(3)

    articles = scroll_until_loaded(driver, min_articles=80, max_scrolls=15)
    print(f"Найдено блоков статей: {len(articles)}")

    fg = FeedGenerator()
    fg.title("Meduza — Статьи")
    fg.link(href=url, rel="alternate")
    fg.description("Новые статьи с сайта Meduza")

    for art in articles:
        try:
            a = art.find_element(By.CSS_SELECTOR, 'a.Link-module-isInBlockTitle')
            href = a.get_attribute('href')
            title = a.text.strip()
            spans = a.find_elements(By.TAG_NAME, 'span')
            description = (
                spans[1].text.strip() if len(spans) > 1
                else (spans[0].text.strip() if spans else "")
            )

            pub_date = extract_date_from_url(href)
            if not pub_date:
                pub_date = datetime.now(timezone.utc)

            fe = fg.add_entry()
            fe.title(title)
            fe.link(href=href)
            fe.description(description)
            fe.pubDate(pub_date)
        except Exception as e:
            print("❌ Ошибка при разборе статьи:", e)
            continue

    driver.quit()
    fg.rss_file("meduza.xml")

if __name__ == "__main__":
    generate()

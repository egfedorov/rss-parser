import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin
import re

def extract_date_from_url(url):
    # Извлекаем дату в формате /2025/07/16/ из URL
    match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
    if match:
        year, month, day = map(int, match.groups())
        return datetime(year, month, day, tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def generate():
    url = "https://baikal-journal.ru/"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    articles = soup.select("article.post-archive, article.post-feature, article.post-large")

    fg = FeedGenerator()
    fg.title("Baikal Journal — Статьи")
    fg.link(href=url, rel="alternate")
    fg.description("Материалы с сайта baikal-journal.ru")
    fg.language("ru")

    for art in articles:
        title_el = art.select_one(".post-archive__title-inner, .post-feature__title, .post-large__title, .post-archive__title")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        link_el = art.select_one("a.card-link, a.post-archive__link")
        if not link_el:
            continue
        link = urljoin(url, link_el["href"])

        desc_el = art.select_one(".post-archive__desc")
        description = desc_el.get_text(strip=True) if desc_el else ""

        # Самое важное — ДАТА из ссылки!
        pub_date = extract_date_from_url(link)

        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.pubDate(pub_date)

    fg.rss_file("baikal.xml")

if __name__ == "__main__":
    generate()

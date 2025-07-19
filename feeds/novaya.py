from bs4 import BeautifulSoup
import requests
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

def generate():
    url = "https://novayagazeta.eu/stories"
    base_url = "https://novayagazeta.eu"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    fg = FeedGenerator()
    fg.id(url)
    fg.title("Новая Газета — Сюжеты")
    fg.link(href=url, rel='alternate')
    fg.description("Лента публикаций из раздела «Сюжеты» на сайте novayagazeta.eu")
    fg.language("ru")

    articles = soup.select("div.alCK3")

    for article in articles[:20]:  # Ограничим до 10
        link_tag = article.select_one("a.TJM_G")
        title_tag = article.select_one("h2")
        desc_tag = article.select_one("span.tkJ0o")
        author_tag = article.select_one("a.CObzH")
        time_tag = article.select_one("article-time")

        if not link_tag or not title_tag:
            continue

        link = base_url + link_tag.get("href")
        title = title_tag.text.strip()
        description = desc_tag.text.strip() if desc_tag else ""
        author = author_tag.text.strip() if author_tag else ""
        timestamp = time_tag.get("date-time")
        pub_date = datetime.fromtimestamp(int(timestamp) / 1000, tz=timezone.utc) if timestamp else datetime.now(timezone.utc)

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.author({'name': author})
        fe.pubDate(pub_date)

    fg.rss_file("feed_novaya.xml")
    print("✅ novaya: сгенерирован feed_novaya.xml")

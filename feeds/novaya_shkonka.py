import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import time

def generate():
    url = "https://novayagazeta.ru/themes/shkonka"
    base_url = "https://novayagazeta.ru"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    fg = FeedGenerator()
    fg.title("Письма со шконки — Новая газета")
    fg.link(href=url, rel="alternate")
    fg.description("Свежие публикации из рубрики «Письма со шконки» на novayagazeta.ru")

    articles = soup.find_all("div", class_="alCK3")
    seen_links = set()

    for article in articles:
        try:
            link_tag = article.find("a", class_="APpOT")
            if not link_tag or not link_tag.get("href"):
                continue

            href = link_tag["href"]
            full_link = base_url + href

            if full_link in seen_links:
                continue
            seen_links.add(full_link)

            title_block = article.find("h2", class_="FTuaH")
            if not title_block:
                continue

            title_b = title_block.find("b").text.strip() if title_block.find("b") else ""
            title_i = title_block.find("i").text.strip() if title_block.find("i") else ""
            title = f"{title_b} — {title_i}" if title_i else title_b

            author_tag = article.find("a", class_="CObzH")
            author = author_tag.text.strip() if author_tag else "Новая газета"

            date_tag = article.find("article-time")
            timestamp = int(date_tag.get("date-time")) / 1000 if date_tag else time.time()
            pub_date = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc)

            description = title_i if title_i else title_b

            fe = fg.add_entry()
            fe.title(title)
            fe.link(href=full_link)
            fe.description(description)
            fe.author(name=author)
            fe.pubDate(pub_date)

        except Exception as e:
            print("⚠️ Ошибка при обработке статьи:", e)
            continue

    fg.rss_file("feed_novaya_shkonka.xml")
    print("✅ novaya_shkonka: сгенерирован feed_novaya_shkonka.xml")

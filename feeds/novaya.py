import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin

def generate():
    url = "https://novayagazeta.eu/stories"
    base_url = "https://novayagazeta.eu"

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    fg = FeedGenerator()
    fg.id(url)
    fg.title("Новая Газета Европа — Сюжеты")
    fg.link(href=url, rel='alternate')
    fg.description("Публикации из раздела «Сюжеты» на сайте novayagazeta.eu")
    fg.language("ru")

    articles = soup.select("div.alCK3")

    seen_links = set()  # чтобы не добавлять повторяющиеся статьи

    for article in articles:
        link_tag = article.select_one("a.APpOT, a.TJM_G")
        if not link_tag or not link_tag.get("href"):
            continue

        link = urljoin(base_url, link_tag["href"])

        # пропускаем, если уже добавляли эту ссылку
        if link in seen_links:
            continue
        seen_links.add(link)

        title_tag = article.select_one("h2.FTuaH")
        title = title_tag.get_text(strip=True) if title_tag else "Без названия"

        desc_tag = article.select_one("span.tkJ0o")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        author_tag = article.select_one("a.CObzH")
        author = author_tag.get_text(strip=True) if author_tag else "Новая газета Европа"

        time_tag = article.select_one("article-time[date-time]")
        if time_tag and time_tag.get("date-time"):
            try:
                timestamp = int(time_tag["date-time"]) / 1000
                pub_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            except ValueError:
                pub_date = datetime.now(timezone.utc)
        else:
            pub_date = datetime.now(timezone.utc)

        img_tag = article.select_one("img")
        img_url = img_tag["src"] if img_tag and img_tag.get("src") else None

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.author({'name': author})
        fe.pubDate(pub_date)
        if img_url:
            fe.enclosure(img_url, 0, "image/jpeg")

    fg.rss_file("feed_novaya.xml")

if __name__ == "__main__":
    generate()

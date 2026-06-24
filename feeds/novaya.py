import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin


def generate():
    URL = "https://novayagazeta.eu/stories"
    BASE_URL = "https://novayagazeta.eu"
    OUTPUT_FILE = "feed_novaya.xml"

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Контейнер со статьями
    container = soup.select_one("#materials-container")
    if not container:
        print("⚠️ novaya: контейнер #materials-container не найден.")
        return

    articles = container.find_all("article")
    if not articles:
        print("⚠️ novaya: статьи не найдены.")
        return

    fg = FeedGenerator()
    fg.id(URL)
    fg.title("Новая Газета Европа — Сюжеты")
    fg.link(href=URL, rel="alternate")
    fg.description("Публикации из раздела «Сюжеты» на сайте novayagazeta.eu")
    fg.language("ru")

    seen_links = set()

    for article in articles:
        # Ссылка и href
        link_tag = article.find("a", href=True)
        if not link_tag:
            continue
        link = urljoin(BASE_URL, link_tag["href"])
        if link in seen_links:
            continue
        seen_links.add(link)

        # Заголовок
        title_el = article.select_one("div.font-extrabold.break-words")
        title = title_el.get_text(strip=True) if title_el else "Без названия"

        # Лид / описание
        lead_el = article.select_one("div.font-lyon")
        description = lead_el.get_text(strip=True) if lead_el else ""

        # Авторы — span с font-medium внутри блока с датой
        author_spans = article.select("span.font-medium")
        authors = [s.get_text(strip=True) for s in author_spans if s.get_text(strip=True)]
        author = ", ".join(authors) if authors else "Новая газета Европа"

        # Дата публикации
        # Приоритет: article-time[date-time] (Unix ms) → <time datetime="">
        pub_date = datetime.now(timezone.utc)
        time_tag = article.find("article-time", attrs={"date-time": True})
        if time_tag:
            try:
                timestamp = int(time_tag["date-time"]) / 1000
                pub_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            except (ValueError, OSError):
                pass
        else:
            time_el = article.find("time", attrs={"datetime": True})
            if time_el:
                try:
                    pub_date = datetime.fromisoformat(
                        time_el["datetime"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

        # Картинка (опционально)
        img_tag = article.select_one("img[src]")
        img_url = img_tag["src"] if img_tag else None

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link(href=link)
        fe.description(description)
        fe.author({"name": author})
        fe.pubDate(pub_date)
        if img_url:
            fe.enclosure(img_url, 0, "image/jpeg")

    fg.rss_file(OUTPUT_FILE)
    print(f"✅ novaya: сгенерирован {OUTPUT_FILE} ({len(seen_links)} статей)")


if __name__ == "__main__":
    generate()

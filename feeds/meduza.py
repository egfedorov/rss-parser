import requests
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

def generate():
    url = "https://meduza.io/api/w5/new_search?chrono=articles&page=0&per_page=24&locale=ru"
    base_url = "https://meduza.io"

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    fg = FeedGenerator()
    fg.title("Meduza — Хроника статей")
    fg.link(href=base_url, rel="alternate")
    fg.description("Свежие статьи из раздела Meduza: Хроника")

    documents = data.get("documents", {})
    for doc_id, item in documents.items():
        try:
            title = item.get("title", "").strip()
            slug = item.get("slug", "")
            pub_date = datetime.fromtimestamp(item.get("published_at", 0)).astimezone(timezone.utc)
            full_link = f"{base_url}/{slug}"

            fe = fg.add_entry()
            fe.title(title)
            fe.link(href=full_link)
            fe.description(title)
            fe.pubDate(pub_date)

        except Exception as e:
            print("⚠️ Ошибка:", e)
            continue

    fg.rss_file("meduza.xml")

generate()

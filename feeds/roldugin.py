import requests, re
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator

API_URL = "https://novayagazeta.ru/api/v1/get/author?id=401576"
BASE = "https://novayagazeta.ru"

def strip_html(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"<[^>]+>", "", s).strip()

def build_url(type_id: str, slug: str) -> str:
    # маппинг разделов; запасной вариант — /articles/
    mapping = {"statja": "articles", "novost": "news", "video": "videos"}
    section = mapping.get(type_id, "articles")
    return f"{BASE}/{section}/{slug}"

def main():
    r = requests.get(API_URL, timeout=20)
    r.raise_for_status()
    data = r.json()

    author = data["author"]
    records = author.get("records", [])

    fg = FeedGenerator()
    fg.title(f"{author['name']} {author['surname']} — Новая газета")
    fg.link(href=f"{BASE}/authors/{author['id']}", rel="alternate")
    fg.description(f"Свежие материалы {author['name']} {author['surname']} на novayagazeta.ru")
    fg.language("ru")

    # по уму — отсортируем по дате и ограничим, чтобы фид не раздувался
    records = sorted(records, key=lambda x: x.get("date", 0), reverse=True)[:40]

    for item in records:
        slug = item.get("slug")
        type_id = item.get("typeId") or ""   # бывает: "statja", "novost", "video"
        if not slug:
            continue

        link = build_url(type_id, slug)
        title = strip_html(item.get("title") or "")
        subtitle = strip_html(item.get("subtitle") or "")
        full_title = f"{title} — {subtitle}" if subtitle else title

        # в API дата часто как миллисекунды since epoch
        ts = item.get("date") or item.get("published")
        if isinstance(ts, int):
            pub_dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        else:
            # если вдруг ISO-строка
            pub_dt = datetime.fromisoformat(ts.replace("Z","+00:00")).astimezone(timezone.utc) if ts else None

        fe = fg.add_entry()
        fe.title(full_title or "Без названия")
        fe.link(href=link)
        fe.guid(link, permalink=True)
        fe.description(subtitle or title or "")
        if pub_dt:
            fe.pubDate(pub_dt)

    fg.rss_file("roldugin.xml", pretty=True)
    print(f"✅ Записей: {len(records)}")

if __name__ == "__main__":
    main()

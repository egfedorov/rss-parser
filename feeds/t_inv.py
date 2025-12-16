import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

BASE = "https://t-invariant.org"
START_URL = BASE + "/texts/"

MAX_ITEMS = 10
ARTICLE_WORKERS = 3
TIMEOUT = (3, 6)

def parse_russian_date(date_str: str) -> datetime:
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    m = re.match(r'(\d{1,2}) ([а-яё]+) (\d{4})', date_str.strip())
    if m:
        day, month_str, year = m.groups()
        return datetime(
            int(year),
            months[month_str],
            int(day),
            12, 0,
            tzinfo=timezone.utc
        )
    return datetime.now(timezone.utc)

def get_pub_date(article_url: str, session: requests.Session) -> datetime:
    try:
        r = session.get(article_url, timeout=TIMEOUT)
        soup = BeautifulSoup(r.text, "html.parser")
        author_date_div = soup.select_one(".t-inv-post-author-and-date")
        if author_date_div:
            anchors = author_date_div.find_all("a")
            if anchors:
                return parse_russian_date(anchors[-1].text)
    except Exception:
        pass
    return datetime.now(timezone.utc)

def generate():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "rss-parser/1.0 (+https://github.com/egfedorov/rss-parser)"
    })

    r = session.get(START_URL, timeout=TIMEOUT)
    soup = BeautifulSoup(r.text, "html.parser")

    articles = []

    for block in soup.select(".t-inv-block-posts"):
        for a in block.select("a[data-wpel-link]"):
            href = a["href"]
            if not href.startswith("http"):
                href = BASE + href

            title_tag = a.select_one(".t-inv-title")
            title = title_tag.get_text(strip=True) if title_tag else "Без названия"

            lead_tag = a.select_one(".t-inv-lead")
            description = lead_tag.get_text(strip=True) if lead_tag else ""

            image = ""
            thumb_tag = a.select_one(".t-inv-thumb")
            if thumb_tag and "style" in thumb_tag.attrs:
                m = re.search(r'background-image:\s*url\(([^)]+)\)', thumb_tag["style"])
                if m:
                    image = m.group(1)

            articles.append({
                "href": href,
                "title": title,
                "description": description,
                "image": image,
            })

            if len(articles) >= MAX_ITEMS:
                break
        if len(articles) >= MAX_ITEMS:
            break

    # --- ПАРАЛЛЕЛЬНО ЗАГРУЖАЕМ ДАТЫ ---
    with ThreadPoolExecutor(max_workers=ARTICLE_WORKERS) as executor:
        future_map = {
            executor.submit(get_pub_date, a["href"], session): a
            for a in articles
        }

        for future in as_completed(future_map):
            article = future_map[future]
            try:
                article["pub_date"] = future.result()
            except Exception:
                article["pub_date"] = datetime.now(timezone.utc)

    fg = FeedGenerator()
    fg.title("T-invariant — Тексты")
    fg.link(href=START_URL)
    fg.description("Главная лента текстов T-invariant")
    fg.language("ru")

    for a in articles:
        fe = fg.add_entry()
        fe.title(a["title"])
        fe.link(href=a["href"])
        fe.pubDate(a["pub_date"])
        if a["description"]:
            fe.description(a["description"])
        if a["image"]:
            fe.enclosure(a["image"], 0, "image/jpeg")

    fg.rss_file("t_inv.xml")

if __name__ == "__main__":
    generate()

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://www.kavkazr.com"
START_URL = BASE + "/p/7647.html"

MAX_ITEMS = 10
ARTICLE_WORKERS = 3
TIMEOUT = (3, 6)

EXCLUDE_PATTERNS = [
    "/a/28482722",
    "/p/",
    "/apps",
    "/about",
    "/subscribe",
    "/info",
    "/mobileapps",
]

def should_exclude(href: str) -> bool:
    return any(p in href for p in EXCLUDE_PATTERNS)

def get_article_date(article_url: str, session: requests.Session) -> datetime:
    try:
        resp = session.get(article_url, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, "html.parser")
        time_tag = soup.select_one("#content time[datetime]")
        if time_tag:
            return datetime.fromisoformat(
                time_tag["datetime"].replace("Z", "+00:00")
            )
    except Exception:
        pass
    return datetime.now(timezone.utc)

def generate():
    session = requests.Session()
    session.headers.update({"User-Agent": "rss-parser/1.0"})

    r = session.get(START_URL, timeout=TIMEOUT)
    soup = BeautifulSoup(r.text, "html.parser")

    articles = []

    for li in soup.select("li"):
        a = li.select_one('a[href*="/a/"]')
        if not a:
            continue

        href = a["href"]
        if not href.startswith("http"):
            href = BASE + href

        if should_exclude(href):
            continue

        title_tag = li.select_one("h4")
        title = title_tag.get_text(strip=True) if title_tag else a.get_text(strip=True)

        img = ""
        img_tag = li.select_one("img")
        if img_tag:
            img = img_tag.get("src") or img_tag.get("data-src") or ""

        articles.append({
            "href": href,
            "title": title,
            "img": img,
        })

        if len(articles) >= MAX_ITEMS:
            break

    # --- ПАРАЛЛЕЛЬНО ЗАБИРАЕМ ДАТЫ ---
    with ThreadPoolExecutor(max_workers=ARTICLE_WORKERS) as executor:
        future_map = {
            executor.submit(get_article_date, a["href"], session): a
            for a in articles
        }

        for future in as_completed(future_map):
            article = future_map[future]
            try:
                article["pub_date"] = future.result()
            except Exception:
                article["pub_date"] = datetime.now(timezone.utc)

    fg = FeedGenerator()
    fg.title("Кавказ.Реалии — Общество")
    fg.link(href=START_URL)
    fg.description('Главная лента раздела "Общество"')
    fg.language("ru")

    for a in articles:
        fe = fg.add_entry()
        fe.id(a["href"])
        fe.title(a["title"])
        fe.link(href=a["href"])
        fe.pubDate(a["pub_date"])
        fe.description(a["title"])
        if a["img"]:
            fe.enclosure(a["img"], 0, "image/jpeg")

    fg.rss_file("kavkaz_soc.xml")

if __name__ == "__main__":
    generate()

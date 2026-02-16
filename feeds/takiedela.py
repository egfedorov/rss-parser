import json
import re
import time
from datetime import timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from feedgen.feed import FeedGenerator


URL = "https://takiedela.ru/stories/"
OUT_FILE = "takiedela.xml"

HEADERS = {
    # Важно: без нормального UA некоторые сайты отдают другой HTML
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

ANTI_BOT_MARKERS = (
    "recaptcha",
    "g-recaptcha",
    "cf-challenge",
    "cloudflare",
    "verify you are human",
)

RU_DATE_RE = re.compile(
    r"\b(\d{1,2}\s+[А-Яа-яЁё]+\s+\d{4})(?:\s*,\s*(\d{1,2}:\d{2}))?",
    re.IGNORECASE,
)


def is_probably_blocked(html: str) -> bool:
    low = html.lower()
    return any(m in low for m in ANTI_BOT_MARKERS)


def fetch(session: requests.Session, url: str, timeout: int = 20) -> str:
    r = session.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    html = r.text

    if is_probably_blocked(html):
        raise RuntimeError("Похоже на антибот/recaptcha-страницу (HTML не тот).")

    # Частый симптом: страница “пустая” или без ключевых блоков
    if len(html) < 10_000:
        # не всегда ошибка, но подозрительно — лучше подсветить
        pass

    return html


def parse_list_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # Самый стабильный якорь в твоём HTML: ссылка-обёртка карточки
    cards = soup.select("a.b-material__txt")
    if not cards:
        # fallback: вдруг классы поменялись частично
        cards = soup.select("ul.b-col-list a[href]")

    items: list[dict] = []

    for a in cards:
        # Внутри a.b-material__txt лежат span.head и span.lead
        title_tag = a.select_one(".b-material__head")
        lead_tag = a.select_one(".b-material__lead")

        href = a.get("href")
        if not href or not title_tag or not lead_tag:
            continue

        title = title_tag.get_text(" ", strip=True)
        description = lead_tag.get_text(" ", strip=True)
        link = urljoin(URL, href)

        items.append(
            {
                "title": title,
                "description": description,
                "link": link,
            }
        )

    return items


def extract_pub_date(article_html: str) -> "datetime|None":
    soup = BeautifulSoup(article_html, "html.parser")

    # 1) Классический вариант: <time datetime="...">
    time_tag = soup.select_one("time[datetime]")
    if time_tag and time_tag.has_attr("datetime"):
        try:
            dt = dateparser.parse(time_tag["datetime"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass

    # 2) OpenGraph / article meta
    meta = soup.select_one('meta[property="article:published_time"][content]')
    if meta and meta.get("content"):
        try:
            dt = dateparser.parse(meta["content"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass

    # 3) JSON-LD (часто у новостных сайтов)
    for script in soup.select('script[type="application/ld+json"]'):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except Exception:
            continue

        def iter_nodes(x):
            if isinstance(x, dict):
                yield x
                for v in x.values():
                    yield from iter_nodes(v)
            elif isinstance(x, list):
                for v in x:
                    yield from iter_nodes(v)

        for node in iter_nodes(data):
            dp = node.get("datePublished") if isinstance(node, dict) else None
            if dp:
                try:
                    dt = dateparser.parse(dp)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt.astimezone(timezone.utc)
                except Exception:
                    pass

    # 4) Последний шанс: русская дата как текст (“16 февраля 2026, 00:00”)
    text = soup.get_text(" ", strip=True)
    m = RU_DATE_RE.search(text)
    if m:
        raw = m.group(1)
        if m.group(2):
            raw = f"{raw}, {m.group(2)}"
        try:
            dt = dateparser.parse(raw, dayfirst=True, fuzzy=True)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass

    return None


def generate():
    session = requests.Session()

    list_html = fetch(session, URL)
    items = parse_list_page(list_html)

    if not items:
        raise RuntimeError(
            "Не нашёл ни одной карточки на странице. "
            "Либо селекторы изменились, либо сайт отдаёт другой HTML для requests."
        )

    fg = FeedGenerator()
    fg.title("Такие дела — Истории")
    fg.link(href=URL, rel="alternate")
    fg.description("Материалы из раздела «Истории» сайта takiedela.ru")
    fg.language("ru")

    for idx, item in enumerate(items, start=1):
        link = item["link"]

        try:
            article_html = fetch(session, link, timeout=20)
        except Exception as e:
            print(f"⚠️ Не удалось открыть статью ({idx}/{len(items)}): {link}\n   {e}")
            continue

        pub_date = extract_pub_date(article_html)
        if not pub_date:
            print(f"‼️ Не удалось определить дату: {link} — пропускаю")
            continue

        fe = fg.add_entry()
        fe.title(item["title"])
        fe.link(href=link)
        fe.description(item["description"])
        fe.pubDate(pub_date)

        # лёгкая вежливость к сайту
        time.sleep(0.2)

    fg.rss_file(OUT_FILE)
    print(f"✅ Готово: {OUT_FILE} (entries: {len(fg.entry())})")


if __name__ == "__main__":
    generate()

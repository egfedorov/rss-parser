import asyncio
from pathlib import Path
import requests
import feedparser
import hashlib

from telegram import send_message
from diff import load_state, save_state, get_new_entries, update_state

FEEDS_FILE = Path("publisher/feeds.txt")
STATE_FILE = Path("publisher/state.json")

MAX_CONCURRENCY = 5
TIMEOUT = 20

# Однократная отправка последних записей для всех RSS
FORCE_SEND_FIRST = True

# Задержка между отправками сообщений в Telegram (иначе 429)
SEND_DELAY = 0.8


# ---------------------- HEADERS ----------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "ru,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


# ---------------------- УНИКАЛЬНЫЙ ID ----------------------
def compute_id(item: dict) -> str:
    raw = (
        (item.get("title") or "") +
        (item.get("link") or "") +
        (item.get("published") or "") +
        (item.get("updated") or "")
    ).encode("utf-8")

    return hashlib.sha1(raw).hexdigest()


# ---------------------- HTTP ЗАГРУЗКА ----------------------
def fetch_blocking(url: str) -> str:
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"❌ Ошибка загрузки {url}: {e}")
        return ""


async def fetch_rss(url: str) -> list:
    xml_text = await asyncio.to_thread(fetch_blocking, url)

    if not xml_text:
        return []

    parsed = feedparser.parse(xml_text)

    entries = []
    for item in parsed.entries:
        entries.append({
            "id": compute_id(item),
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "summary": item.get("summary", ""),
            "published": item.get("published", ""),
        })

    return entries


# ---------------------- ФОРМАТИРОВАНИЕ СООБЩЕНИЙ ----------------------
def format_entry(entry: dict) -> str:
    title = entry["title"].strip()
    link = entry["link"].strip()
    summary = entry.get("summary", "").strip()

    if summary:
        return f"{title}\n{summary}\n{link}"
    return f"{title}\n{link}"


async def send_with_rate_limit(text: str):
    await asyncio.to_thread(send_message, text)
    await asyncio.sleep(SEND_DELAY)


# ---------------------- ОБРАБОТКА ЛЕНТЫ ----------------------
async def process_feed(url: str, state: dict, sem: asyncio.Semaphore):
    async with sem:
        entries = await fetch_rss(url)

    if not entries:
        print(f"⚠️ Пропущено (нет записей или ошибка): {url}")
        return

    last_id = state.get(url)
    first_id = entries[0]["id"]

    # ---- ОДНОКРАТНАЯ РАССЫЛКА ПОСЛЕДНЕЙ ЗАПИСИ ----
    if last_id is None and FORCE_SEND_FIRST:
        print(f"🚀 Первый запуск: отправляем последнюю запись — {url}")
        await send_with_rate_limit(format_entry(entries[0]))
        state[url] = first_id
        return

    # ---- Обычный режим DIFF ----
    new_entries = get_new_entries(url, entries, state)

    if not new_entries:
        print(f"— Нет новых записей: {url}")
        update_state(url, entries, state)
        return

    print(f"✨ Новых записей: {len(new_entries)} — {url}")

    # отправляем старые → новые (хронологически)
    for entry in reversed(new_entries):
        await send_with_rate_limit(format_entry(entry))

    update_state(url, entries, state)


# ---------------------- MAIN ----------------------
async def main_async():
    feeds = [
        line.strip()
        for line in FEEDS_FILE.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

    print(f"📡 Всего RSS-лент: {len(feeds)}")

    state = load_state(STATE_FILE)
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    tasks = [process_feed(url, state, sem) for url in feeds]
    await asyncio.gather(*tasks)

    save_state(STATE_FILE, state)

    print("✅ Готово. Все обновления отправлены.")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

import asyncio
from pathlib import Path
import requests
import feedparser

from telegram import send_message
from diff import load_state, save_state, get_new_entries, update_state

FEEDS_FILE = Path("publisher/feeds.txt")
STATE_FILE = Path("publisher/state.json")

MAX_CONCURRENCY = 5
TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}


def fetch_blocking(url: str) -> str:
    """Синхронная загрузка RSS (будет вызвана через asyncio.to_thread)."""
    resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
    resp.raise_for_status()
    return resp.text


async def fetch_rss(url: str) -> list:
    """Асинхронная загрузка RSS через поток."""
    try:
        xml_text = await asyncio.to_thread(fetch_blocking, url)
    except Exception as e:
        print(f"❌ Ошибка загрузки {url}: {e}")
        return []

    parsed = feedparser.parse(xml_text)

    entries = []
    for item in parsed.entries:
        entry_id = item.get("id") or item.get("link")
        if not entry_id:
            continue

        entries.append({
            "id": entry_id,
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "summary": item.get("summary", "")
        })

    return entries


def format_entry(entry: dict) -> str:
    """Формирует текст сообщения."""
    title = entry["title"].strip()
    link = entry["link"].strip()
    summary = entry.get("summary", "").strip()

    if summary:
        return f"{title}\n{summary}\n{link}"
    return f"{title}\n{link}"


async def process_feed(url: str, state: dict, sem: asyncio.Semaphore):
    """Загружает RSS, ищет новые записи, отправляет их и обновляет state."""

    async with sem:
        entries = await fetch_rss(url)

    if not entries:
        return

    # Найти новые записи через diff.py
    new_entries = get_new_entries(url, entries, state)

    if not new_entries:
        print(f"— Нет новых записей: {url}")
        # Но state всё равно обновляем на самый свежий id
        update_state(url, entries, state)
        return

    print(f"✨ Новых записей: {len(new_entries)} — {url}")

    # Отправляем в порядке от старых к новым
    for entry in reversed(new_entries):
        await asyncio.to_thread(send_message, format_entry(entry))

    # Обновляем state
    update_state(url, entries, state)


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

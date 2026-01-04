import asyncio
from pathlib import Path
import json
import requests
import feedparser

from telegram import send_message

FEEDS_FILE = Path("publisher/feeds.txt")
STATE_FILE = Path("publisher/state.json")

MAX_CONCURRENCY = 5
TIMEOUT = 15


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def fetch_blocking(url: str) -> str:
    resp = requests.get(url, timeout=TIMEOUT)
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
    title = entry["title"]
    link = entry["link"]
    summary = entry.get("summary", "")

    if summary:
        return f"{title}\n{summary}\n{link}"
    return f"{title}\n{link}"


async def process_feed(url: str, state: dict, sem: asyncio.Semaphore):
    async with sem:
        entries = await fetch_rss(url)

    if not entries:
        return

    last_id = state.get(url)
    first_id = entries[0]["id"]

    # Первый запуск: просто запоминаем
    if last_id is None:
        state[url] = first_id
        print(f"📌 Первый запуск: {url}")
        return

    # Собираем новые записи
    new = []
    for entry in entries:
        if entry["id"] == last_id:
            break
        new.append(entry)

    if not new:
        print(f"— Нет новых записей: {url}")
        state[url] = first_id
        return

    # Отправляем новые записи в правильном порядке
    for entry in reversed(new):
        await asyncio.to_thread(send_message, format_entry(entry))

    print(f"✨ Новых записей: {len(new)} — {url}")
    state[url] = first_id


async def main_async():
    feeds = [
        line.strip()
        for line in FEEDS_FILE.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

    state = load_state()
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    tasks = [process_feed(url, state, sem) for url in feeds]
    await asyncio.gather(*tasks)

    save_state(state)
    print("✅ Готово.")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

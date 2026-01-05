import asyncio
from pathlib import Path
import requests
import feedparser

from telegram import send_message
from diff import load_state, save_state, get_new_entries, update_state

FEEDS_FILE = Path("publisher/feeds.txt")
STATE_FILE = Path("publisher/state.json")

MAX_CONCURRENCY = 5
TIMEOUT = 20  # немного увеличили для сайтов с Cloudflare

# -------------------------------------------------------------------
# УСИЛЕННЫЕ HEADERS (маскируют GitHub Actions под настоящий браузер)
# -------------------------------------------------------------------

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
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Dest": "document",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


# -----------------------------
# DEBUG helper
# -----------------------------
def debug_state(title: str, state: dict):
    print(f"\n🔍 {title}:")
    print(f"STATE_FILE = {STATE_FILE.absolute()}")
    print(f"EXISTS = {STATE_FILE.exists()}")
    try:
        size = STATE_FILE.stat().st_size
    except FileNotFoundError:
        size = 0
    print(f"FILE SIZE = {size} bytes")
    print(f"STATE CONTENT = {state}\n")


def fetch_blocking(url: str) -> str:
    """Синхронная загрузка RSS (работает внутри asyncio.to_thread)."""

    try:
        resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        return resp.text

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP {e.response.status_code} при загрузке {url}")
        return ""
    except Exception as e:
        print(f"❌ Ошибка загрузки {url}: {e}")
        return ""


async def fetch_rss(url: str) -> list:
    """Асинхронная загрузка RSS через поток."""
    xml_text = await asyncio.to_thread(fetch_blocking, url)

    if not xml_text:
        print(f"⚠️ DEBUG: xml_text пустой для {url}")
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

    print(f"📘 DEBUG: {url} → entries: {len(entries)}")
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
    """Загружает RSS, ищет новые записи, отправляет их в Telegram."""

    async with sem:
        entries = await fetch_rss(url)

    if not entries:
        print(f"⚠️ Пропущено (нет записей или ошибка): {url}")
        return

    new_entries = get_new_entries(url, entries, state)

    # Нет новых записей
    if not new_entries:
        print(f"— Нет новых записей: {url}")
        update_state(url, entries, state)
        return

    # Отправляем новые записи (от старых к новым)
    print(f"✨ Новых записей: {len(new_entries)} — {url}")

    for entry in reversed(new_entries):
        await asyncio.to_thread(send_message, format_entry(entry))

    update_state(url, entries, state)


async def main_async():
    feeds = [
        line.strip()
        for line in FEEDS_FILE.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

    print(f"📡 Всего RSS-лент: {len(feeds)}")

    # ---------- DEBUG BEFORE ----------
    state = load_state(STATE_FILE)
    debug_state("Перед запуском", state)

    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    tasks = [process_feed(url, state, sem) for url in feeds]
    await asyncio.gather(*tasks)

    save_state(STATE_FILE, state)

    # ---------- DEBUG AFTER ----------
    new_state = load_state(STATE_FILE)
    debug_state("После сохранения", new_state)

    print("✅ Готово. Все обновления отправлены.")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

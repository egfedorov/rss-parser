from pathlib import Path
import feedparser
from telegram import send_message
from diff import load_state, save_state, get_new_entries, update_state

FEEDS_FILE = Path("publisher/feeds.txt")
STATE_FILE = Path("publisher/state.json")


def load_feeds():
    """Читает список RSS из feeds.txt, игнорирует пустые строки и комментарии."""
    return [
        line.strip()
        for line in FEEDS_FILE.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def format_entry(e):
    """Форматирование сообщения в телеграме."""
    title = e.get("title", "").strip()
    link = e.get("link", "").strip()
    summary = e.get("summary", "").strip()

    # Можно расширить формат, если нужно
    if summary:
        return f"{title}\n{summary}\n{link}"
    else:
        return f"{title}\n{link}"


def process_feed(feed_url, state):
    """Загружает RSS, определяет новые записи и отправляет в Telegram."""
    parsed = feedparser.parse(feed_url)

    entries = []
    for item in parsed.entries:
        entries.append({
            "id": item.get("id") or item.get("link"),
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "summary": item.get("summary", ""),
        })

    new_entries = get_new_entries(feed_url, entries, state)

    for e in new_entries:
        text = format_entry(e)
        send_message(text)

    update_state(feed_url, new_entries, state)


def main():
    feeds = load_feeds()
    state = load_state(STATE_FILE)

    for url in feeds:
        try:
            print(f"📡 Обрабатываем: {url}")
            process_feed(url, state)
        except Exception as e:
            print(f"❌ Ошибка при обработке {url}: {e}")

    save_state(STATE_FILE, state)
    print("✅ Готово. Все обновления отправлены.")


if __name__ == "__main__":
    main()

import json
from pathlib import Path


def load_state(path: Path) -> dict:
    """
    Загружает state.json.
    Возвращает плоский словарь вида:
    {
        "url1": "last_id",
        "url2": "last_id",
        ...
    }
    """
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text())
    except Exception:
        # Если state повреждён — лучше сбросить
        return {}


def save_state(path: Path, state: dict):
    """Сохраняет state.json в красивом виде."""
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def get_new_entries(feed_url: str, entries: list, state: dict):
    """
    Возвращает новые записи фида.

    entries — список dict:
    {
        "id": str,
        "title": str,
        "link": str,
        "summary": str
    }
    """

    if not entries:
        return []

    first_id = entries[0]["id"]
    last_id = state.get(feed_url)

    # Первый запуск — запоминаем свежую запись
    if last_id is None:
        state[feed_url] = first_id
        return []

    # Ищем новые записи до last_id
    new = []
    for item in entries:
        if item["id"] == last_id:
            break
        new.append(item)

    return new


def update_state(feed_url: str, entries: list, state: dict):
    """Записывает id самой свежей записи."""
    if entries:
        state[feed_url] = entries[0]["id"]

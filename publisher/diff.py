import json
from pathlib import Path


def load_state(path: Path) -> dict:
    """
    Загружает state.json.
    Если файл отсутствует — возвращает пустой словарь.
    """
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text())
    except Exception:
        # Если state поврежден — обнуляем, чтобы не ломать работу бота
        return {}


def save_state(path: Path, state: dict):
    """
    Сохраняет state.json в удобочитаемом виде.
    """
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def get_new_entries(feed_url: str, entries: list, state: dict):
    """
    Определяет новые записи для заданного фида.

    entries — список словарей вида:
    {
        "id": "...",
        "title": "...",
        "link": "...",
        "summary": "..."
    }
    """

    # id последней отправленной записи
    last_id = state.get(feed_url)

    # первая (самая свежая) запись
    if not entries:
        return []

    first_entry_id = entries[0]["id"]

    # Если фид запускается впервые — просто запоминаем
    if last_id is None:
        state[feed_url] = first_entry_id
        return []

    # Ищем новые записи: всё, что идет ДО last_id
    new = []
    for item in entries:
        if item["id"] == last_id:
            break
        new.append(item)

    return new


def update_state(feed_url: str, entries: list, state: dict):
    """
    Обновляет state после отправки записей.
    Просто запоминаем id самой свежей записи.
    """

    if entries:
        # самая свежая запись — первая
        state[feed_url] = entries[0]["id"]

import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # например: -1001234567890

if not TOKEN:
    raise RuntimeError("Не задан TELEGRAM_TOKEN в env")

if not CHAT_ID:
    raise RuntimeError("Не задан CHAT_ID в env")


def send_message(text: str):
    """Отправляет текстовое сообщение в Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False,
    }

    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()

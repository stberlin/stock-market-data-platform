import requests

from src.logging_config import get_logger

logger = get_logger(__name__)


def send_telegram_message(message: str, bot_token: str, chat_id: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }

    response = requests.post(
        url,
        data=payload,
        timeout=10,
    )

    if response.status_code != 200:
        logger.error(
            "Telegram API error: %s",
            response.text,
        )

    response.raise_for_status()

    return response.json()

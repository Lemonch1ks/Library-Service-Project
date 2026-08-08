import json
import logging
from urllib import error, request

from django.conf import settings


logger = logging.getLogger(__name__)


def send_telegram_message(text):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        logger.warning("Telegram credentials are not configured.")
        return False

    url = f"https: //api.telegram.org/bot{token}/sendMessage"

    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
        }
    ).encode("utf-8")

    telegram_request = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(telegram_request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("ok", False)
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        logger.exception("Telegram notification failed.")
        return False

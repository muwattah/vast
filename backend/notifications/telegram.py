import logging
from backend.notifications.base import NotificationProvider
from backend.config import get_settings
logger = logging.getLogger(__name__)

class TelegramProvider(NotificationProvider):
    name = "telegram"
    def available(self) -> bool:
        s = get_settings()
        return bool(getattr(s, "telegram_bot_token", None) and getattr(s, "telegram_chat_id", None))
    def send(self, title: str, body: str, **kwargs) -> bool:
        if not self.available():
            logger.info("Telegram provider unavailable — skipped")
            return False
        logger.info(f"Telegram would send: {title}")
        return True

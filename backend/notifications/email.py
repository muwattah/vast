import logging
from backend.notifications.base import NotificationProvider
from backend.config import get_settings
logger = logging.getLogger(__name__)

class EmailProvider(NotificationProvider):
    name = "email"
    def available(self) -> bool:
        s = get_settings()
        return bool(getattr(s, "smtp_host", None) and getattr(s, "smtp_user", None))
    def send(self, title: str, body: str, **kwargs) -> bool:
        if not self.available():
            logger.info("Email provider unavailable — skipped")
            return False
        logger.info(f"Email would send: {title}")
        return True

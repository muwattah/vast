from typing import Optional
from sqlalchemy.orm import Session
from backend.models.property import Notification
from backend.notifications.email import EmailProvider
from backend.notifications.telegram import TelegramProvider
import logging
logger = logging.getLogger(__name__)

def notify(db: Session, title: str, body: str, property_id: Optional[int] = None,
           saved_search_id: Optional[int] = None) -> Notification:
    n = Notification(title=title, body=body, property_id=property_id, saved_search_id=saved_search_id)
    db.add(n)
    db.commit()
    db.refresh(n)
    for provider in (EmailProvider(), TelegramProvider()):
        try:
            if provider.available():
                provider.send(title, body)
        except Exception as e:
            logger.warning(f"Provider {provider.name} failed: {e}")
    return n

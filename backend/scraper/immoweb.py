"""
Immoweb scraper stub.
Live scraping is intentionally not implemented:
- Violates typical ToS
- Heavy anti-bot protection
Use official channels, RSS, or paid data partners when available.
"""
from .base_scraper import BaseScraper, ScrapedProperty
from typing import List
import logging

logger = logging.getLogger(__name__)


class ImmowebScraper(BaseScraper):
    source_name = "immoweb"

    async def search(self, postcodes: list[str], max_pages: int = 3) -> List[ScrapedProperty]:
        logger.warning("Immoweb live scraper is disabled (ToS / anti-bot). Returning empty list.")
        return []

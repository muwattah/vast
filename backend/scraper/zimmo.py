from .base_scraper import BaseScraper, ScrapedProperty
from typing import List
import logging
logger = logging.getLogger(__name__)

class ZimmoScraper(BaseScraper):
    source_name = "zimmo"
    async def search(self, postcodes: list[str], max_pages: int = 3) -> List[ScrapedProperty]:
        logger.warning("Zimmo live scraper is disabled. Returning empty list.")
        return []

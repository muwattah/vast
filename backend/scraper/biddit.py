from .base_scraper import BaseScraper, ScrapedProperty
from typing import List
import logging
logger = logging.getLogger(__name__)

class BidditScraper(BaseScraper):
    source_name = "biddit"
    async def search(self, postcodes: list[str], max_pages: int = 3) -> List[ScrapedProperty]:
        logger.warning("Biddit live scraper is disabled. Returning empty list.")
        return []

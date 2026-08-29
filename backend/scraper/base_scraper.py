"""
Base scraper interface.
All concrete scrapers must implement the same output structure.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ScrapedProperty:
    source: str
    source_listing_id: str
    url: str
    title: str
    price: float | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    district: str | None = None
    property_type: str | None = None
    living_area: float | None = None
    total_area: float | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    year_built: int | None = None
    epc_label: str | None = None
    epc_score: float | None = None
    description: str | None = None
    images: list = field(default_factory=list)
    features: list = field(default_factory=list)
    is_to_renovate: bool = False
    is_fully_to_renovate: bool = False
    is_investment: bool = False
    raw: dict = field(default_factory=dict)


class BaseScraper(ABC):
    source_name: str = "base"

    @abstractmethod
    async def search(self, postcodes: list[str], max_pages: int = 3) -> List[ScrapedProperty]:
        """Return a list of normalized ScrapedProperty objects."""
        pass

    def respect_robots(self) -> bool:
        """Override if you have checked robots.txt and ToS."""
        return False

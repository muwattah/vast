"""
Central configuration using pydantic-settings.
All sensitive keys stay in environment variables.
"""
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/antwerp_properties.db"
    openai_api_key: str = ""
    grok_api_key: str = ""
    environment: str = "development"

    max_price: float = 800000
    min_area: float = 50
    target_postcodes: str = "2000,2018,2020,2030,2040,2050,2060,2100,2140,2150,2160,2170,2180,2600,2610,2620,2630,2640,2650,2660"
    ai_score_threshold: float = 6.0

    renovation_cost_light_min: float = 300
    renovation_cost_light_max: float = 600
    renovation_cost_medium_min: float = 600
    renovation_cost_medium_max: float = 1000
    renovation_cost_heavy_min: float = 1000
    renovation_cost_heavy_max: float = 1500

    scrape_rate_limit_seconds: float = 2.0
    enable_scrapers: bool = False
    use_demo_data: bool = True

    weight_margin: float = 0.30
    weight_price: float = 0.25
    weight_renovation: float = 0.20
    weight_diy: float = 0.15
    weight_location: float = 0.10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def postcodes(self) -> List[str]:
        return [p.strip() for p in self.target_postcodes.split(",") if p.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()

from abc import ABC, abstractmethod
from typing import Optional
from backend.ai.schemas import AnalysisResult


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    def analyze(self, prop_data: dict) -> Optional[AnalysisResult]:
        """Return validated AnalysisResult or None on failure."""
        pass

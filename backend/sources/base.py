from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum

class SourceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    REQUIRES_PARTNER = "REQUIRES_PARTNER"
    BLOCKED = "BLOCKED"
    IMPORT_ONLY = "IMPORT_ONLY"
    ERROR = "ERROR"

@dataclass
class FetchResult:
    source: str
    status: str
    discovered: int = 0
    parsed: int = 0
    rejected: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)
    duration_ms: int = 0
    items: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""

class BaseSource(ABC):
    name: str = "base"
    status: SourceStatus = SourceStatus.DISABLED
    method: str = "unknown"
    description: str = ""
    @abstractmethod
    def fetch(self, limit: int = 20, **kwargs) -> FetchResult:
        pass

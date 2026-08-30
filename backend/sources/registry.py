from typing import Dict, List, Any
from datetime import datetime
from backend.sources.base import BaseSource, FetchResult
_REGISTRY: Dict[str, BaseSource] = {}
_LAST_RUNS: Dict[str, Dict[str, Any]] = {}

def register(source: BaseSource) -> None:
    _REGISTRY[source.name] = source
def get_source(name: str):
    return _REGISTRY.get(name)
def list_sources() -> List[Dict[str, Any]]:
    out = []
    for name, src in _REGISTRY.items():
        last = _LAST_RUNS.get(name, {})
        out.append({"source": name, "status": src.status.value, "method": src.method,
                    "description": src.description, "last_run": last.get("timestamp"),
                    "last_result": last.get("result")})
    return out
def record_run(name: str, result: FetchResult) -> None:
    _LAST_RUNS[name] = {"timestamp": datetime.utcnow().isoformat() + "Z",
        "result": {"status": result.status, "discovered": result.discovered, "parsed": result.parsed,
                   "rejected": result.rejected, "inserted": result.inserted, "updated": result.updated,
                   "skipped": result.skipped, "duration_ms": result.duration_ms,
                   "message": result.message, "errors": result.errors[:5]}}
def init_registry() -> None:
    if _REGISTRY: return
    from backend.sources.csv_source import CsvImportSource
    from backend.sources.json_source import JsonImportSource
    from backend.sources.immoweb import ImmowebSource
    from backend.sources.zimmo import ZimmoSource
    from backend.sources.immovlan import ImmovlanSource
    from backend.sources.biddit import BidditSource
    from backend.sources.url_import import UrlImportSource
    for s in (CsvImportSource(), JsonImportSource(), ImmowebSource(), ZimmoSource(),
              ImmovlanSource(), BidditSource(), UrlImportSource()):
        register(s)

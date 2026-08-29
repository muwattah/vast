"""JSON importer – accepts list of objects or {properties: [...]}."""
import json
from typing import List, Dict, Any
from .base_importer import BaseImporter


class JsonImporter(BaseImporter):
    source_name = "import"

    def parse(self, content: bytes | str, filename: str = "") -> List[Dict[str, Any]]:
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        data = json.loads(content)
        if isinstance(data, dict):
            rows = data.get("properties") or data.get("listings") or data.get("items") or [data]
        elif isinstance(data, list):
            rows = data
        else:
            raise ValueError("JSON must be a list of properties or an object with 'properties' key")
        return [self.normalize_row(r, source="import") for r in rows if isinstance(r, dict)]

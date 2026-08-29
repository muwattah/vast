"""CSV importer – expects header row with flexible column names."""
import csv
import io
from typing import List, Dict, Any
from .base_importer import BaseImporter


class CsvImporter(BaseImporter):
    source_name = "import"

    def parse(self, content: bytes | str, filename: str = "") -> List[Dict[str, Any]]:
        if isinstance(content, bytes):
            content = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            return []
        return [self.normalize_row(r, source="import") for r in rows]

from backend.sources.base import BaseSource, SourceStatus, FetchResult
class CsvImportSource(BaseSource):
    name = "csv_import"
    status = SourceStatus.ACTIVE
    method = "IMPORT_ONLY"
    description = "User CSV via Import Center — primary real-data path."
    def fetch(self, limit=20, **kwargs):
        return FetchResult(source=self.name, status=self.status.value, message="Use POST /api/import/preview + /confirm")

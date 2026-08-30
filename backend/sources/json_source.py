from backend.sources.base import BaseSource, SourceStatus, FetchResult
class JsonImportSource(BaseSource):
    name = "json_import"
    status = SourceStatus.ACTIVE
    method = "IMPORT_ONLY"
    description = "User JSON via Import Center."
    def fetch(self, limit=20, **kwargs):
        return FetchResult(source=self.name, status=self.status.value, message="Use POST /api/import/json")

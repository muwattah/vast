from backend.sources.base import BaseSource, SourceStatus, FetchResult
class ImmovlanSource(BaseSource):
    name = "immovlan"
    status = SourceStatus.NOT_SUPPORTED
    method = "PUBLIC_HTML"
    description = "Not implemented (ToS/anti-bot). Use CSV/JSON import."
    def fetch(self, limit=20, **kwargs):
        return FetchResult(source=self.name, status=self.status.value, message=self.description)

from backend.sources.base import BaseSource, SourceStatus, FetchResult
class ZimmoSource(BaseSource):
    name = "zimmo"
    status = SourceStatus.NOT_SUPPORTED
    method = "PUBLIC_HTML"
    description = "Cloudflare challenge. Use CSV/JSON import."
    def fetch(self, limit=20, **kwargs):
        return FetchResult(source=self.name, status=self.status.value, message=self.description)

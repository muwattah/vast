from backend.sources.base import BaseSource, SourceStatus, FetchResult
class ImmowebSource(BaseSource):
    name = "immoweb"
    status = SourceStatus.NOT_SUPPORTED
    method = "REQUIRES_PARTNER"
    description = "Cloudflare-blocked. Partner API is publish-only. Use CSV/JSON import."
    def fetch(self, limit=20, **kwargs):
        return FetchResult(source=self.name, status=self.status.value, message=self.description)

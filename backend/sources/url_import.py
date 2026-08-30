import re
from datetime import datetime
from urllib.request import Request, urlopen
from backend.sources.base import BaseSource, SourceStatus, FetchResult

USER_AGENT = "VastgoedInvestorBot/1.0 (+https://github.com/muwattah/vast)"

def fetch_url_listing(url: str):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    meta = {}
    for m in re.finditer(r'<meta\s+property=["\']og:(\w+)["\']\s+content=["\']([^"\']*)["\']', html, re.I):
        meta[m.group(1).lower()] = m.group(2)
    title = meta.get("title") or ""
    if not title:
        tm = re.search(r"<title>([^<]+)</title>", html, re.I)
        title = tm.group(1).strip() if tm else url
    desc = meta.get("description") or ""
    combined = f"{title} {desc}"
    pc_m = re.search(r"\b(2[0-6]\d{2})\b", combined)
    price_m = re.search(r"€\s*([\d.\s]+)", combined)
    area_m = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]", combined, re.I)
    price = float(re.sub(r"[^\d]", "", price_m.group(1))) if price_m else None
    area = float(area_m.group(1).replace(",", ".")) if area_m else None
    source = "url_import"
    if "biddit.be" in url: source = "biddit"
    return {"source": source, "source_listing_id": re.sub(r"\W+", "_", url)[-80:],
            "url": url, "title": title, "description": desc,
            "postal_code": pc_m.group(1) if pc_m else None,
            "price": price, "living_area": area,
            "images": [meta["image"]] if meta.get("image") else [],
            "property_type": "huis", "observed_at": datetime.utcnow(),
            "is_to_renovate": "renov" in combined.lower()}

class UrlImportSource(BaseSource):
    name = "url_import"
    status = SourceStatus.ACTIVE
    method = "PUBLIC_HTML"
    description = "Single public URL import via Open Graph meta."
    def fetch(self, limit=1, url="", **kwargs):
        if not url:
            return FetchResult(source=self.name, status=self.status.value, message="Provide url=")
        try:
            item = fetch_url_listing(url)
            return FetchResult(source=self.name, status=self.status.value, discovered=1, parsed=1, items=[item], message="OK")
        except Exception as e:
            return FetchResult(source=self.name, status=SourceStatus.ERROR.value, errors=[str(e)], message=str(e))

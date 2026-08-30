"""Biddit connector — sitemap + Open Graph. Rate-limited. Antwerp PC filter."""
import re, time, logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from backend.sources.base import BaseSource, SourceStatus, FetchResult
from backend.sources.antwerp import in_antwerp_area, ANTWERP_POSTCODES

logger = logging.getLogger(__name__)
SITEMAP_NL = "https://www.biddit.be/stg/eco/nl_sitemap_1.xml"
USER_AGENT = "VastgoedInvestorBot/1.0 (+https://github.com/muwattah/vast; polite; rate-limited)"
REQUEST_DELAY_SEC = 1.5
TIMEOUT = 20

def _http_get(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xml"})
    with urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")

def _extract_detail_ids(sitemap_xml: str, limit: int) -> List[str]:
    ids = re.findall(r"/catalog/detail/(\d+)", sitemap_xml)
    seen, out = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i); out.append(i)
        if len(out) >= limit: break
    return out

def _parse_og(html: str) -> Dict[str, str]:
    meta = {}
    for m in re.finditer(r'<meta\s+property=["\']og:(\w+)["\']\s+content=["\']([^"\']*)["\']', html, re.I):
        meta[m.group(1).lower()] = m.group(2)
    return meta

def _parse_postcode(text: str) -> Optional[str]:
    for m in re.finditer(r"\b(\d{4})\b", text or ""):
        if m.group(1) in ANTWERP_POSTCODES:
            return m.group(1)
    return None

def _parse_area(text: str) -> Optional[float]:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]", text or "", re.I)
    return float(m.group(1).replace(",", ".")) if m else None

def _parse_price(text: str) -> Optional[float]:
    m = re.search(r"€\s*([\d.\s]+)", text or "")
    if m:
        raw = re.sub(r"[^\d]", "", m.group(1))
        if raw: return float(raw)
    return None

class BidditSource(BaseSource):
    name = "biddit"
    status = SourceStatus.ACTIVE
    method = "PUBLIC_HTML"
    description = "Public auction listings via official sitemap + OG meta. Rate-limited. Antwerp PC filter."

    def fetch(self, limit: int = 10, antwerp_only: bool = True, **kwargs) -> FetchResult:
        t0 = time.time()
        result = FetchResult(source=self.name, status=self.status.value)
        try:
            xml = _http_get(SITEMAP_NL)
            ids = _extract_detail_ids(xml, limit=min(limit * 15, 120))
            result.discovered = len(ids)
            items = []
            for i, sid in enumerate(ids):
                if len(items) >= limit: break
                url = f"https://www.biddit.be/nl/catalog/detail/{sid}"
                try:
                    if i > 0: time.sleep(REQUEST_DELAY_SEC)
                    html = _http_get(url)
                    og = _parse_og(html)
                    title = og.get("title") or f"Biddit listing {sid}"
                    desc = og.get("description") or ""
                    combined = f"{title} {desc}"
                    pc = _parse_postcode(combined)
                    city = "Antwerpen" if "antwerp" in combined.lower() else None
                    if antwerp_only and not in_antwerp_area(pc, city):
                        result.rejected += 1
                        continue
                    item = {
                        "source": "biddit", "source_listing_id": sid, "url": url,
                        "title": title, "description": desc, "postal_code": pc,
                        "city": city or ("Antwerpen" if pc else None),
                        "price": _parse_price(combined), "living_area": _parse_area(combined),
                        "property_type": "huis",
                        "images": [og["image"]] if og.get("image") else [],
                        "is_to_renovate": any(x in combined.lower() for x in ["renovatie", "te renoveren"]),
                        "observed_at": datetime.utcnow(),
                    }
                    items.append(item)
                    result.parsed += 1
                except (URLError, HTTPError, TimeoutError) as e:
                    result.errors.append(f"{sid}: {e}")
                    result.rejected += 1
            result.items = items
            result.message = f"Parsed {result.parsed} Antwerp-area candidates from sitemap+OG (limit={limit})."
        except Exception as e:
            result.status = SourceStatus.ERROR.value
            result.errors.append(str(e))
            result.message = f"Biddit fetch failed: {e}"
        result.duration_ms = int((time.time() - t0) * 1000)
        return result

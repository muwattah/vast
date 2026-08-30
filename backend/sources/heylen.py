"""Heylen Vastgoed — public HTML + schema.org RealEstateListing JSON-LD."""
import re, json, time, logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin
from backend.sources.base import BaseSource, SourceStatus, FetchResult
from backend.sources.antwerp import is_antwerp_postcode

logger = logging.getLogger(__name__)
BASE = "https://www.heylenvastgoed.be"
LISTING_INDEX = f"{BASE}/kopen"
USER_AGENT = "VastgoedInvestorBot/1.0 (+https://github.com/muwattah/vast; polite; rate-limited)"
REQUEST_DELAY_SEC = 1.2
TIMEOUT = 25

def _http_get(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html", "Accept-Language": "nl-BE,nl;q=0.9"})
    with urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")

def _extract_listing_urls(index_html: str) -> List[str]:
    urls, seen = [], set()
    for m in re.finditer(r'href=["\'](/kopen/[^"\']+/\d+)["\']', index_html, re.I):
        path = m.group(1)
        if path not in seen:
            seen.add(path)
            urls.append(urljoin(BASE, path))
    return urls

def _parse_json_ld(html: str) -> List[dict]:
    out = []
    for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I|re.S):
        try:
            data = json.loads(m.group(1).strip())
            out.extend(data if isinstance(data, list) else [data])
        except json.JSONDecodeError:
            continue
    return out

def _find_real_estate_listing(blocks: List[dict]) -> Optional[dict]:
    for b in blocks:
        if isinstance(b, dict) and b.get("@type") == "RealEstateListing":
            return b
        if isinstance(b, dict) and "@graph" in b:
            for g in b["@graph"]:
                if isinstance(g, dict) and g.get("@type") == "RealEstateListing":
                    return g
    return None

def _parse_area_from_text(text: str) -> Optional[float]:
    if not text: return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]", text, re.I)
    return float(m.group(1).replace(",", ".")) if m else None

def parse_heylen_detail(html: str, url: str) -> Optional[Dict[str, Any]]:
    listing = _find_real_estate_listing(_parse_json_ld(html))
    if not listing: return None
    field_provenance = {}
    title = listing.get("name") or ""
    description = listing.get("description") or ""
    images = []
    img = listing.get("image")
    if isinstance(img, str): images = [img]
    elif isinstance(img, list): images = [i for i in img if isinstance(i, str)]
    price = None
    offers = listing.get("offers") or {}
    if isinstance(offers, dict) and offers.get("price") is not None:
        try:
            price = float(offers["price"])
            field_provenance["price"] = "JSON-LD RealEstateListing.offers.price"
        except (TypeError, ValueError):
            price = None
    address = listing.get("address") or {}
    postal_code = address.get("postalCode") if isinstance(address, dict) else None
    city = address.get("addressLocality") if isinstance(address, dict) else None
    street = address.get("streetAddress") if isinstance(address, dict) else None
    if postal_code: field_provenance["postal_code"] = "JSON-LD PostalAddress.postalCode"
    if city: field_provenance["city"] = "JSON-LD PostalAddress.addressLocality"
    living_area = _parse_area_from_text(description) or _parse_area_from_text(html)
    if living_area: field_provenance["living_area"] = "text parse"
    ptype = "huis"
    ul = url.lower()
    if "appartement" in ul: ptype = "appartement"
    elif "grond" in ul: ptype = "grond"
    elif "opbrengst" in ul: ptype = "opbrengsteigendom"
    field_provenance.update({"property_type": "URL slug", "title": "JSON-LD name", "description": "JSON-LD description"})
    if images: field_provenance["images"] = "JSON-LD image"
    sid_m = re.search(r"/(\d+)/?$", url.rstrip("/"))
    source_id = sid_m.group(1) if sid_m else re.sub(r"\W+", "_", url)[-40:]
    return {
        "source": "heylen", "source_listing_id": source_id, "url": url,
        "title": title or f"Heylen {source_id}", "description": description,
        "price": price, "postal_code": str(postal_code) if postal_code else None,
        "city": city, "address": street, "living_area": living_area,
        "property_type": ptype, "images": images,
        "is_to_renovate": any(x in (description or "").lower() for x in ["renovatie", "te renoveren", "opknapper"]),
        "observed_at": datetime.utcnow(), "field_provenance": field_provenance,
    }

def data_quality(item: Dict[str, Any]) -> str:
    checks = [item.get("price") is not None, bool(item.get("postal_code")),
              item.get("living_area") is not None, bool(item.get("description")),
              bool(item.get("images")), bool(item.get("property_type"))]
    score = sum(1 for c in checks if c)
    return "HIGH" if score >= 5 else ("MEDIUM" if score >= 3 else "LOW")

def is_analyzable(item: Dict[str, Any]) -> bool:
    return item.get("price") is not None and float(item.get("price") or 0) > 0

class HeylenSource(BaseSource):
    name = "heylen"
    status = SourceStatus.ACTIVE
    method = "PUBLIC_HTML"
    description = "Heylen Vastgoed via schema.org RealEstateListing JSON-LD. Rate-limited. Antwerp PC filter."

    def fetch(self, limit: int = 15, antwerp_only: bool = True, **kwargs) -> FetchResult:
        t0 = time.time()
        result = FetchResult(source=self.name, status=self.status.value)
        try:
            urls = _extract_listing_urls(_http_get(LISTING_INDEX))
            result.discovered = len(urls)
            items, checked = [], 0
            for url in urls:
                if len(items) >= limit: break
                try:
                    if checked > 0: time.sleep(REQUEST_DELAY_SEC)
                    html = _http_get(url)
                    checked += 1
                    item = parse_heylen_detail(html, url)
                    if not item:
                        result.rejected += 1
                        continue
                    if antwerp_only and not is_antwerp_postcode(item.get("postal_code")):
                        result.rejected += 1
                        continue
                    item["data_quality"] = data_quality(item)
                    item["analyzable"] = is_analyzable(item)
                    items.append(item)
                    result.parsed += 1
                except (URLError, HTTPError, TimeoutError) as e:
                    result.errors.append(f"{url}: {e}")
                    result.rejected += 1
            result.items = items
            wp = sum(1 for i in items if i.get("price"))
            wa = sum(1 for i in items if i.get("living_area"))
            an = sum(1 for i in items if i.get("analyzable"))
            result.message = f"Heylen: discovered={result.discovered} checked={checked} antwerp={result.parsed} with_price={wp} with_area={wa} analyzable={an}"
        except Exception as e:
            result.status = SourceStatus.ERROR.value
            result.errors.append(str(e))
            result.message = f"Heylen fetch failed: {e}"
        result.duration_ms = int((time.time() - t0) * 1000)
        return result

"""Heylen Vastgoed — embedded RSC listing records from public /kopen page."""
from __future__ import annotations
import re, json, logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.request import Request, urlopen
from urllib.parse import urljoin
from backend.sources.base import BaseSource, SourceStatus, FetchResult
from backend.sources.antwerp import is_antwerp_postcode

logger = logging.getLogger(__name__)
BASE = "https://www.heylenvastgoed.be"
LISTING_INDEX = f"{BASE}/kopen"
USER_AGENT = "VastgoedInvestorBot/1.0 (+https://github.com/muwattah/vast; polite; rate-limited)"
TIMEOUT = 40

PROP_RE = re.compile(
    r'\\"ID\\":(\d+),' 
    r'\\"Goal\\":(\d+),' 
    r'\\"Street\\":\\"((?:[^\\"\\\\]|\\\\.)*)\\",' 
    r'\\"HouseNumber\\":(\\"(?:[^\\"\\\\]|\\\\.)*\\"|null),' 
    r'\\"BoxNr\\":(\\"(?:[^\\"\\\\]|\\\\.)*\\"|null),' 
    r'\\"Zip\\":\\"(\d{4})\\",' 
    r'\\"City\\":\\"((?:[^\\"\\\\]|\\\\.)*)\\",' 
    r'\\"Price\\":\\"(\d+)\\",' 
    r'\\"NumberOfBedRooms\\":(\d+|null),' 
    r'\\"NumberOfBathRooms\\":(\d+|null),' 
    r'\\"SurfaceTotal\\":(\d+|null),' 
    r'\\"SurfaceGround2\\":(\d+|null),' 
    r'\\"Status\\":(\d+),' 
    r'\\"SubStatus\\":(\d+|null),' 
    r'\\"WebID\\":\\"([^\\"]*)\\",' 
    r'\\"EPCLabelText\\":(\\"([^\\"]*)\"|null),' 
    r'\\"CreatedDate\\":\\"([^\\"]*)\\",' 
    r'\\"ProjectID\\":(null|\d+),' 
    r'\\"SiteID\\":(\d+),' 
    r'\\"LastChangedDate\\":\\"([^\\"]*)\\",' 
    r'\\"GoogleX\\":\\"([^\\"]*)\\",' 
    r'\\"GoogleY\\":\\"([^\\"]*)\\"' 
    r'.{0,300}?' 
    r'\\"ConstructionYear\\":(\d+|null)',
    re.DOTALL,
)

def _http_get(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html", "Accept-Language": "nl-BE,nl;q=0.9"})
    with urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")

def _unquote_field(raw: str) -> Optional[str]:
    if raw is None or raw == "null": return None
    s = raw.strip()
    if s.startswith('\\"') and s.endswith('\\"'): s = s[2:-2]
    elif s.startswith('"') and s.endswith('"'): s = s[1:-1]
    return s or None

def _to_int(raw) -> Optional[int]:
    if raw is None or raw == "null": return None
    try: return int(str(raw).strip().strip('"').replace('\\"', ""))
    except (TypeError, ValueError): return None

def data_quality(item: Dict[str, Any]) -> str:
    checks = [item.get("price") is not None, bool(item.get("postal_code")),
              item.get("living_area") is not None, bool(item.get("epc_label")),
              item.get("bedrooms") is not None, bool(item.get("address"))]
    score = sum(1 for c in checks if c)
    return "HIGH" if score >= 5 else ("MEDIUM" if score >= 3 else "LOW")

def is_analyzable(item: Dict[str, Any]) -> bool:
    return item.get("price") is not None and float(item.get("price") or 0) > 0 and item.get("living_area") is not None and float(item.get("living_area") or 0) > 0

def parse_embedded_listings(html: str) -> List[Dict[str, Any]]:
    seen, items = set(), []
    for m in PROP_RE.finditer(html):
        (pid, goal, street, house, box, zipc, city, price, beds, baths, surface, ground,
         status, substatus, webid, epc_full, epc_label, created, project, site, changed, gx, gy, year) = m.groups()
        if pid in seen: continue
        seen.add(pid)
        price_i, surface_i = _to_int(price), _to_int(surface)
        epc = _unquote_field(epc_full) if epc_full and epc_full != "null" else (epc_label or None)
        if epc == "null": epc = None
        house_n, box_n = _unquote_field(house), _unquote_field(box)
        address_parts = [street]
        if house_n: address_parts.append(house_n)
        if box_n: address_parts.append(f"bus {box_n}")
        address = " ".join(address_parts)
        beds_i, baths_i = _to_int(beds), _to_int(baths)
        ptype = "appartement" if (surface_i and surface_i < 90 and (beds_i or 0) <= 2) else "huis"
        try:
            lat = float(gx) if gx else None
            lon = float(gy) if gy else None
        except ValueError:
            lat = lon = None
        city_slug = (city or "antwerpen").lower().replace(" ", "-")
        item = {
            "source": "heylen", "source_listing_id": str(pid),
            "url": f"{BASE}/kopen/te-koop-in-{city_slug}/{pid}",
            "title": f"{ptype.capitalize()} in {city}" if city else f"Heylen {pid}",
            "description": f"{address}, {zipc} {city}".strip(),
            "price": float(price_i) if price_i else None,
            "postal_code": zipc, "city": city, "address": address,
            "living_area": float(surface_i) if surface_i else None,
            "bedrooms": beds_i, "bathrooms": baths_i,
            "epc_label": epc.upper() if epc else None,
            "year_built": _to_int(year), "latitude": lat, "longitude": lon,
            "property_type": ptype, "images": [], "observed_at": datetime.utcnow(),
            "field_provenance": {
                "price": "heylen_embedded_rsc", "postal_code": "heylen_embedded_rsc",
                "living_area": "heylen_embedded_rsc.SurfaceTotal",
                "epc_label": "heylen_embedded_rsc.EPCLabelText",
            },
        }
        item["data_quality"] = data_quality(item)
        item["analyzable"] = is_analyzable(item)
        items.append(item)
    return items

def parse_heylen_detail(html: str, url: str) -> Optional[Dict[str, Any]]:
    blocks = []
    for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I|re.S):
        try:
            data = json.loads(m.group(1).strip())
            blocks.extend(data if isinstance(data, list) else [data])
        except json.JSONDecodeError:
            continue
    listing = None
    for b in blocks:
        if isinstance(b, dict) and b.get("@type") == "RealEstateListing": listing = b; break
        if isinstance(b, dict) and "@graph" in b:
            for g in b["@graph"]:
                if isinstance(g, dict) and g.get("@type") == "RealEstateListing": listing = g; break
    if not listing: return None
    offers = listing.get("offers") or {}
    price = float(offers["price"]) if isinstance(offers, dict) and offers.get("price") is not None else None
    addr = listing.get("address") or {}
    pc = addr.get("postalCode") if isinstance(addr, dict) else None
    city = addr.get("addressLocality") if isinstance(addr, dict) else None
    street = addr.get("streetAddress") if isinstance(addr, dict) else None
    desc = listing.get("description") or ""
    area_m = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]", desc, re.I)
    living_area = float(area_m.group(1).replace(",", ".")) if area_m else None
    sid_m = re.search(r"/(\d+)/?$", url.rstrip("/"))
    img = listing.get("image")
    images = [img] if isinstance(img, str) else []
    item = {"source": "heylen", "source_listing_id": sid_m.group(1) if sid_m else url[-40:],
            "url": url, "title": listing.get("name") or "Heylen", "description": desc,
            "price": price, "postal_code": str(pc) if pc else None, "city": city, "address": street,
            "living_area": living_area, "images": images,
            "property_type": "appartement" if "appartement" in url.lower() else "huis",
            "observed_at": datetime.utcnow(), "field_provenance": {"price": "JSON-LD"}}
    item["data_quality"] = data_quality(item)
    item["analyzable"] = is_analyzable(item)
    return item

def _extract_listing_urls(index_html: str) -> List[str]:
    urls, seen = [], set()
    for m in re.finditer(r'href=["\'](/kopen/[^"\']+/\d+)["\']', index_html, re.I):
        path = m.group(1)
        if path not in seen:
            seen.add(path); urls.append(urljoin(BASE, path))
    return urls

class HeylenSource(BaseSource):
    name = "heylen"
    status = SourceStatus.ACTIVE
    method = "PUBLIC_HTML"
    description = "Heylen: embedded RSC records on /kopen (price, m2, EPC, beds, coords). Antwerp filter."

    def fetch(self, limit: int = 500, antwerp_only: bool = True, **kwargs) -> FetchResult:
        import time
        t0 = time.time()
        result = FetchResult(source=self.name, status=self.status.value)
        try:
            html = _http_get(LISTING_INDEX)
            all_items = parse_embedded_listings(html)
            result.discovered = len(all_items)
            items = []
            for item in all_items:
                if antwerp_only and not is_antwerp_postcode(item.get("postal_code")):
                    result.rejected += 1; continue
                items.append(item)
                if len(items) >= limit: break
            result.parsed = len(items)
            result.items = items
            wp = sum(1 for i in items if i.get("price"))
            wa = sum(1 for i in items if i.get("living_area"))
            we = sum(1 for i in items if i.get("epc_label"))
            an = sum(1 for i in items if i.get("analyzable"))
            result.message = f"Heylen embedded: discovered={result.discovered} antwerp={result.parsed} with_price={wp} with_area={wa} with_epc={we} analyzable={an}"
        except Exception as e:
            result.status = SourceStatus.ERROR.value
            result.errors.append(str(e))
            result.message = f"Heylen fetch failed: {e}"
        result.duration_ms = int((time.time() - t0) * 1000)
        return result

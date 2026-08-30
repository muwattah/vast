"""Walls Vastgoedmakelaars — public /tekoop HTML cards."""
from __future__ import annotations
import re, time, logging
from datetime import datetime
from typing import List, Dict, Any
from urllib.request import Request, urlopen
from backend.sources.base import BaseSource, SourceStatus, FetchResult
from backend.sources.antwerp import is_antwerp_postcode

logger = logging.getLogger(__name__)
BASE = "https://www.walls.be"
INDEX = f"{BASE}/tekoop"
USER_AGENT = "VastgoedInvestorBot/1.0 (+https://github.com/muwattah/vast; polite; rate-limited)"
TIMEOUT = 30

CARD_RE = re.compile(
    r'id="(\d+)"[^>]*data-whise-id="(\d+)"[^>]*>.*?'
    r'href="(/tekoop/\d+/[^"]+/?)".*?'
    r'<div class="type">\s*([^<]+?)\s*</div>.*?'
    r'<div class="price">\s*€\s*([\d.\s]+)\s*</div>.*?'
    r'<div class="location">\s*(\d{4})\s+([^<]+?)\s*</div>',
    re.S,
)

def _http_get(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html", "Accept-Language": "nl-BE,nl;q=0.9"})
    with urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")

def parse_index(html: str) -> List[Dict[str, Any]]:
    seen, items = set(), []
    for m in CARD_RE.finditer(html):
        mid, _w, href, ptype, price_raw, pc, city = m.groups()
        if mid in seen: continue
        seen.add(mid)
        price = int(re.sub(r"[^\d]", "", price_raw) or 0) or None
        items.append({
            "source": "walls", "source_listing_id": mid, "url": BASE + href,
            "title": f"{ptype.strip()} in {city.strip()}",
            "property_type": ptype.strip().lower(),
            "price": float(price) if price else None,
            "postal_code": pc, "city": city.strip(),
            "living_area": None, "epc_label": None, "images": [],
            "observed_at": datetime.utcnow(),
            "field_provenance": {"price": "walls_html_card", "postal_code": "walls_html_card"},
            "analyzable": False, "data_quality": "MEDIUM" if price and pc else "LOW",
        })
    return items

def enrich_detail(item: Dict[str, Any]) -> Dict[str, Any]:
    try:
        html = _http_get(item["url"])
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]", html)
        if m:
            item["living_area"] = float(m.group(1).replace(",", "."))
            item["field_provenance"]["living_area"] = "walls_detail_text"
        m = re.search(r"EPC[^A-G]{0,20}([A-G]\+?)", html, re.I)
        if m:
            item["epc_label"] = m.group(1).upper()
            item["field_provenance"]["epc_label"] = "walls_detail_text"
        if item.get("price") and item.get("living_area"):
            item["analyzable"] = True
            item["data_quality"] = "HIGH"
    except Exception as e:
        logger.warning("Walls enrich failed %s: %s", item.get("url"), e)
    return item

class WallsSource(BaseSource):
    name = "walls"
    status = SourceStatus.ACTIVE
    method = "PUBLIC_HTML"
    description = "Walls.be /tekoop cards (price+PC). Optional detail enrich for m2/EPC."

    def fetch(self, limit: int = 150, antwerp_only: bool = True, enrich: bool = False, enrich_limit: int = 20, **kwargs) -> FetchResult:
        t0 = time.time()
        result = FetchResult(source=self.name, status=self.status.value)
        try:
            all_items = parse_index(_http_get(INDEX))
            result.discovered = len(all_items)
            items = []
            for item in all_items:
                if antwerp_only and not is_antwerp_postcode(item.get("postal_code")):
                    result.rejected += 1; continue
                items.append(item)
                if len(items) >= limit: break
            if enrich:
                for i, item in enumerate(items[:enrich_limit]):
                    if i > 0: time.sleep(1.2)
                    enrich_detail(item)
            result.parsed = len(items)
            result.items = items
            wp = sum(1 for i in items if i.get("price"))
            wa = sum(1 for i in items if i.get("living_area"))
            an = sum(1 for i in items if i.get("analyzable"))
            result.message = f"Walls: discovered={result.discovered} antwerp={result.parsed} with_price={wp} with_area={wa} analyzable={an} enrich={enrich}"
        except Exception as e:
            result.status = SourceStatus.ERROR.value
            result.errors.append(str(e))
            result.message = str(e)
        result.duration_ms = int((time.time() - t0) * 1000)
        return result

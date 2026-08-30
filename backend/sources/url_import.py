"""Import a single public listing URL via JSON-LD + Open Graph."""
import re, json
from datetime import datetime
from urllib.request import Request, urlopen
from backend.sources.base import BaseSource, SourceStatus, FetchResult

USER_AGENT = "VastgoedInvestorBot/1.0 (+https://github.com/muwattah/vast)"

def _parse_json_ld(html: str):
    out = []
    pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    for m in re.finditer(pattern, html, re.I | re.S):
        try:
            data = json.loads(m.group(1).strip())
            out.extend(data if isinstance(data, list) else [data])
        except json.JSONDecodeError:
            continue
    return out

def _find_rel(blocks):
    for b in blocks:
        if isinstance(b, dict) and b.get("@type") == "RealEstateListing":
            return b
        if isinstance(b, dict) and "@graph" in b:
            for g in b["@graph"]:
                if isinstance(g, dict) and g.get("@type") == "RealEstateListing":
                    return g
    return None

def fetch_url_listing(url: str):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urlopen(req, timeout=25) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    provenance = {}
    listing = _find_rel(_parse_json_ld(html))
    title = desc = None
    price = postal_code = city = street = None
    images = []
    if listing:
        title = listing.get("name")
        desc = listing.get("description")
        provenance["title"] = provenance["description"] = "JSON-LD"
        offers = listing.get("offers") or {}
        if isinstance(offers, dict) and offers.get("price") is not None:
            price = float(offers["price"])
            provenance["price"] = "JSON-LD"
        addr = listing.get("address") or {}
        if isinstance(addr, dict):
            postal_code = addr.get("postalCode")
            city = addr.get("addressLocality")
            street = addr.get("streetAddress")
            if postal_code: provenance["postal_code"] = "JSON-LD"
        img = listing.get("image")
        if isinstance(img, str):
            images = [img]
            provenance["images"] = "JSON-LD"
    meta = {}
    for m in re.finditer(r'<meta\s+property=["\']og:(\w+)["\']\s+content=["\']([^"\']*)["\']', html, re.I):
        meta[m.group(1).lower()] = m.group(2)
    if not title and meta.get("title"):
        title = meta["title"]; provenance["title"] = "OG"
    if not desc and meta.get("description"):
        desc = meta["description"]; provenance["description"] = "OG"
    if not images and meta.get("image"):
        images = [meta["image"]]; provenance["images"] = "OG"
    if not title:
        tm = re.search(r"<title>([^<]+)</title>", html, re.I)
        title = tm.group(1).strip() if tm else url
    combined = f"{title or ''} {desc or ''}"
    if not postal_code:
        pc_m = re.search(r"\b(2[0-6]\d{2})\b", combined)
        if pc_m:
            postal_code = pc_m.group(1); provenance["postal_code"] = "text"
    if price is None:
        price_m = re.search(r"€\s*([\d.\s]+)", combined)
        if price_m:
            raw = re.sub(r"[^\d]", "", price_m.group(1))
            if raw:
                price = float(raw); provenance["price"] = "text"
    area_m = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]", combined, re.I)
    living_area = float(area_m.group(1).replace(",", ".")) if area_m else None
    if living_area: provenance["living_area"] = "text"
    source = "url_import"
    if "biddit.be" in url: source = "biddit"
    elif "heylenvastgoed" in url: source = "heylen"
    return {
        "source": source, "source_listing_id": re.sub(r"\W+", "_", url)[-80:],
        "url": url, "title": title, "description": desc,
        "postal_code": str(postal_code) if postal_code else None,
        "city": city, "address": street, "price": price, "living_area": living_area,
        "images": images, "property_type": "appartement" if "appartement" in url.lower() else "huis",
        "observed_at": datetime.utcnow(), "is_to_renovate": "renov" in combined.lower(),
        "field_provenance": provenance,
        "analyzable": price is not None and float(price or 0) > 0,
        "data_quality": "HIGH" if price and postal_code and (living_area or desc) else ("MEDIUM" if price else "LOW"),
    }

class UrlImportSource(BaseSource):
    name = "url_import"
    status = SourceStatus.ACTIVE
    method = "PUBLIC_HTML"
    description = "Single public URL import via JSON-LD + Open Graph."
    def fetch(self, limit=1, url="", **kwargs):
        if not url:
            return FetchResult(source=self.name, status=self.status.value, message="Provide url=")
        try:
            item = fetch_url_listing(url)
            return FetchResult(source=self.name, status=self.status.value, discovered=1, parsed=1, items=[item], message="OK")
        except Exception as e:
            return FetchResult(source=self.name, status=SourceStatus.ERROR.value, errors=[str(e)], message=str(e))

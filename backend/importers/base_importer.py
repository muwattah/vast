"""
Base importer: normalize external data into Property-compatible dicts.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import re


def make_content_hash(data: Dict[str, Any]) -> str:
    raw = "|".join([
        str(data.get("price") or ""),
        str(data.get("living_area") or ""),
        str(data.get("epc_label") or ""),
        (data.get("description") or "")[:300],
        str(data.get("title") or "")[:100],
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def detect_renovation_flags(text: str) -> Dict[str, bool]:
    t = (text or "").lower()
    return {
        "is_to_renovate": any(x in t for x in [
            "te renoveren", "renovatie", "opknapper", "op te frissen",
            "te moderniseren", "kluswoning", "renovatieplicht",
        ]),
        "is_fully_to_renovate": any(x in t for x in [
            "volledig te renoveren", "totaal te renoveren", "casco",
            "grondig te renoveren", "volledige renovatie",
        ]),
        "is_to_modernize": "te moderniseren" in t or "op te frissen" in t,
        "is_casco": "casco" in t,
        "is_investment": any(x in t for x in [
            "opbrengsteigendom", "opbrengst", "meergezins", "studenten",
            "units", "appartementen",
        ]),
    }


def normalize_epc(label: Optional[str]) -> Optional[str]:
    if not label:
        return None
    s = str(label).upper().strip()
    m = re.search(r"(?:EPC[:\s]*)?([A-F]\+?)(?:\b|$)", s)
    if m:
        return m.group(1)
    return None


class BaseImporter(ABC):
    source_name: str = "import"

    @abstractmethod
    def parse(self, content: bytes | str, filename: str = "") -> List[Dict[str, Any]]:
        pass

    def normalize_row(self, row: Dict[str, Any], source: str = "import") -> Dict[str, Any]:
        def g(*keys, default=None):
            for k in keys:
                if k in row and row[k] not in (None, ""):
                    return row[k]
            return default

        title = str(g("title", "Titel", "name", "naam") or "Geïmporteerd pand")
        description = str(g("description", "beschrijving", "omschrijving", "text") or "")
        flags = detect_renovation_flags(f"{title} {description}")

        price = g("price", "prijs", "vraagprijs", "asking_price")
        try:
            price = float(str(price).replace("€", "").replace(".", "").replace(",", ".").strip()) if price is not None else None
        except (ValueError, TypeError):
            price = None

        area = g("living_area", "bewoonbare_opp", "oppervlakte", "m2", "area", "surface")
        try:
            area = float(str(area).replace(",", ".").replace("m²", "").replace("m2", "").strip()) if area is not None else None
        except (ValueError, TypeError):
            area = None

        data = {
            "source": source,
            "source_listing_id": str(g("source_listing_id", "id", "ref", "referentie") or ""),
            "url": str(g("url", "link", "href") or f"import://{source}/{g('source_listing_id', 'id', default='unknown')}"),
            "title": title,
            "price": price,
            "address": g("address", "adres", "straat"),
            "postal_code": str(g("postal_code", "postcode", "zip") or "")[:10] or None,
            "city": g("city", "gemeente", "stad") or "Antwerpen",
            "district": g("district", "wijk", "buurt"),
            "property_type": (g("property_type", "type", "pandtype") or "huis").lower(),
            "living_area": area,
            "total_area": None,
            "bedrooms": int(g("bedrooms", "slaapkamers", "slpk") or 0) or None,
            "bathrooms": int(g("bathrooms", "badkamers") or 0) or None,
            "year_built": int(g("year_built", "bouwjaar") or 0) or None,
            "epc_label": normalize_epc(g("epc_label", "epc", "EPC")),
            "epc_score": None,
            "description": description,
            "images": g("images", "fotos") if isinstance(g("images", "fotos"), list) else [],
            "features": g("features") if isinstance(g("features"), list) else [],
            **flags,
            "is_active": True,
        }
        if not data["source_listing_id"]:
            data["source_listing_id"] = make_content_hash(data)
        data["content_hash"] = make_content_hash(data)
        return data

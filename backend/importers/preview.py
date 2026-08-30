"""Import preview, validation and column mapping."""
from typing import List, Dict, Any, Optional, Tuple
import re, csv, io
from backend.importers.json_importer import JsonImporter
from backend.importers.csv_importer import CsvImporter

DEFAULT_FIELD_ALIASES = {
    "address": ["address", "adres", "straat", "Address", "Adres"],
    "price": ["price", "prijs", "vraagprijs", "Price", "Prijs"],
    "living_area": ["living_area", "oppervlakte", "area", "m2", "bewoonbare_opp", "Area"],
    "postal_code": ["postal_code", "postcode", "zip", "Postal code", "Postcode"],
    "epc_label": ["epc_label", "epc", "EPC", "Epc"],
    "description": ["description", "beschrijving", "Description"],
    "url": ["url", "link", "URL", "Url"],
    "title": ["title", "titel", "Title", "Titel", "name"],
    "property_type": ["property_type", "type", "Type", "pandtype"],
    "bedrooms": ["bedrooms", "slaapkamers", "Bedrooms"],
    "city": ["city", "gemeente", "stad", "City"],
    "year_built": ["year_built", "bouwjaar", "Year"],
}

def apply_mapping(row, mapping):
    out = {}
    for col, field in mapping.items():
        if col in row and row[col] not in (None, ""):
            out[field] = row[col]
    return out

def auto_detect_mapping(headers):
    mapping = {}
    lower_headers = {h.lower().strip(): h for h in headers}
    for field, aliases in DEFAULT_FIELD_ALIASES.items():
        for a in aliases:
            key = a.lower().strip()
            if key in lower_headers:
                mapping[lower_headers[key]] = field
                break
    return mapping

def validate_row(row, index):
    errors, warnings = [], []
    price = row.get("price")
    if price is None or price == "":
        errors.append(f"Row {index}: price is missing")
    else:
        try:
            p = float(re.sub(r"[^\d.]", "", str(price).replace(",", ".")) or 0)
            if p <= 0:
                errors.append(f"Row {index}: price must be > 0")
        except (ValueError, TypeError):
            errors.append(f"Row {index}: price is not a number")
    area = row.get("living_area")
    if area is not None and area != "":
        try:
            a = float(str(area).replace(",", ".").replace("m²", "").replace("m2", "").strip())
            if a <= 0:
                warnings.append(f"Row {index}: living_area = 0 or negative")
        except (ValueError, TypeError):
            warnings.append(f"Row {index}: living_area is not a number")
    else:
        warnings.append(f"Row {index}: living_area missing")
    pc = row.get("postal_code")
    if pc and not re.match(r"^\d{4}$", str(pc).strip()):
        warnings.append(f"Row {index}: postal_code format unusual ({pc})")
    if not row.get("epc_label"):
        warnings.append(f"Row {index}: EPC unknown")
    return errors, warnings

def preview_import(content, kind="json", mapping=None, filename=""):
    if kind == "csv":
        importer = CsvImporter()
        text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames or []
        raw_rows = list(reader)
        if mapping is None:
            mapping = auto_detect_mapping(headers)
        mapped = [apply_mapping(r, mapping) for r in raw_rows]
        items = [importer.normalize_row(m, source="import") for m in mapped]
    else:
        importer = JsonImporter()
        items = importer.parse(content, filename)
        headers = list(items[0].keys()) if items else []
        mapping = mapping or {}
    errors, warnings, valid_items = [], [], []
    for i, item in enumerate(items, start=1):
        e, w = validate_row(item, i)
        errors.extend(e)
        warnings.extend(w)
        if not e:
            valid_items.append(item)
    preview_rows = [{"title": i.get("title"), "price": i.get("price"),
        "living_area": i.get("living_area"), "postal_code": i.get("postal_code"),
        "epc_label": i.get("epc_label")} for i in valid_items[:10]]
    return {
        "file_detected": True, "kind": kind, "headers": headers, "mapping": mapping,
        "rows_found": len(items), "valid": len(valid_items), "invalid": len(items) - len(valid_items),
        "errors": errors[:50], "warnings": warnings[:50], "preview": preview_rows, "items": valid_items,
    }

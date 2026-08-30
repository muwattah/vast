# Real data sources

| Source | Status | Notes |
|--------|--------|-------|
| **heylen** | ACTIVE | schema.org RealEstateListing JSON-LD with price + postcode |
| **biddit** | ACTIVE | Sitemap+OG; price often UNKNOWN |
| csv/json/url_import | ACTIVE | User-driven |
| immoweb/zimmo/immovlan | NOT_SUPPORTED | Cloudflare/ToS — no anti-bot bypass |

## Live Heylen (2026-08-30)

```
discovered: 24
checked: 24
Antwerp PC: 2
with price: 2
analyzable: 2
stored: 2
```

Examples: Berchem 2600 apt €209k; Hoboken 2660 huis €565k.

```bash
curl -X POST "http://localhost:8000/api/sources/heylen/run?limit=20"
curl "http://localhost:8000/api/properties?exclude_demo=true&source=heylen"
```

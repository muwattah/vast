# Real data sources

| Source | Status | Antwerp volume |
|--------|--------|----------------|
| **heylen** | ACTIVE | **561** price, **522** analyzable (price+m2), **521** EPC |
| biddit | ACTIVE | OG often missing price |
| csv/json/url | ACTIVE | User import |
| immoweb/zimmo/immovlan | NOT_SUPPORTED | No anti-bot bypass |

## Live Heylen (2026-08-30)

```
discovered: 2534
Antwerp: 561
with price: 561
with living_area: 522
with EPC: 521
analyzable: 522
```

```bash
curl -X POST "http://localhost:8000/api/sources/heylen/run?limit=600"
curl "http://localhost:8000/api/properties?exclude_demo=true&source=heylen"
```

# Real data sources — status (2026-08-30)

| Source | Status | Method | Notes |
|--------|--------|--------|-------|
| **csv_import** | ACTIVE | IMPORT_ONLY | Primary path for real listings |
| **json_import** | ACTIVE | IMPORT_ONLY | Primary path for real listings |
| **url_import** | ACTIVE | PUBLIC_HTML | Single URL via Open Graph meta |
| **biddit** | ACTIVE | PUBLIC_HTML | Sitemap + OG tags; rate-limited; Antwerp PC filter |
| **immoweb** | NOT_SUPPORTED | REQUIRES_PARTNER | Cloudflare 403; partner API is publish-only |
| **zimmo** | NOT_SUPPORTED | PUBLIC_HTML | Cloudflare challenge |
| **immovlan** | NOT_SUPPORTED | PUBLIC_HTML | Not implemented (ToS/anti-bot) |

## How to load REAL DATA

1. CSV/JSON via Import Center
2. `POST /api/import/url` with a public listing URL
3. `POST /api/sources/biddit/run?limit=20`
4. List with `?exclude_demo=true`

## Rules
No Cloudflare/CAPTCHA bypass. No login scraping. ARV requires comparables.

# Vast

**Live UI (GitHub Pages):** https://muwattah.github.io/vast/

> Pages host alleen de frontend. Start de API lokaal met uvicorn. In de banner kun je de API-URL instellen (default `http://127.0.0.1:8000/api`).

Antwerp Property Investor — vastgoed deal analyzer voor renovatie/DIY in Antwerpen.

## Architectuur

```
Imports / agency connectors (Heylen, Walls, …)
  → normalisatie → duplicate check → database
  → comparables → valuation → financials → max bid → dashboard
```

- **Geen** Immoweb/Zimmo/Immovlan scraping (Cloudflare / ToS).
- Actieve bronnen: Heylen, Walls, CSV/JSON/URL-import, Biddit (beperkt).
- DEMO-data is altijd gemarkeerd.
- ARV zonder echte comparables = onvoldoende gegevens.

## Installatie

### Linux / macOS
```bash
git clone https://github.com/muwattah/vast.git && cd vast
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export PYTHONPATH=.
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Windows
```cmd
git clone https://github.com/muwattah/vast.git
cd vast
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
set PYTHONPATH=.
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Real data ophalen
```bash
curl -X POST "http://localhost:8000/api/sources/heylen/run?limit=600"
curl -X POST "http://localhost:8000/api/sources/walls/run?limit=150"
curl "http://localhost:8000/api/properties?exclude_demo=true&limit=20"
```

### Docker
```bash
docker compose up --build
```

### GitHub Pages
Settings → Pages → Source: **Deploy from branch** → Branch `main` → folder **/docs**.

## Tests
```bash
export PYTHONPATH=.
python3 tests/test_core.py
python3 tests/test_valuation.py
python3 tests/test_heylen.py
```

## Belangrijke endpoints
- `GET /api/properties`, `/api/deals`, `/api/sources`
- `POST /api/sources/{heylen|walls|biddit}/run`
- `POST /api/import/json`, `/api/import/csv`, `/api/import/url`
- `GET /health`, `/docs`

# Antwerp Property Investor

**Vastgoed Deal Analyzer voor Antwerpen** — vind, waardeer en beoordeel renovatiepanden met focus op DIY-investering.

> *Is dit pand interessant om te kopen, hoeveel kan ik maximaal bieden, en hoeveel marge blijft er over als ik zoveel mogelijk zelf renoveer?*

## Architectuur

```
Imports (JSON/CSV/manual) → Normalisatie → Duplicate check → Database
     ↓
Comparables → Valuation engine (ARV) → Financial engine → Deal analysis → Max bid
     ↓
AI interpretation (optional) → Dashboard / API
```

- **Geen live scraping** van Immoweb/Zimmo/Immovlan (disabled stubs).
- **Geen verzonnen marktdata** — ARV vereist opgeslagen comparables.
- DEMO-data is altijd duidelijk gemarkeerd.

## Installatie

### Linux / macOS

```bash
git clone https://github.com/muwattah/vast.git
cd vast
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export PYTHONPATH=.
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (andere terminal):

```bash
cd frontend && python3 -m http.server 3000
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

### Docker

```bash
docker compose up --build
```

## Tests

```bash
export PYTHONPATH=.
python3 tests/test_core.py
python3 tests/test_valuation.py
python3 tests/test_phase4_plus.py
```

## Belangrijke endpoints

- GET /api/properties, /api/properties/{id}/deal, /api/deals
- POST /api/import/json, /api/import/csv, /api/import/comparables
- POST /api/tools/max-bid, /api/tools/scenario
- GET /api/tools/compare?ids=1,2
- GET/POST /api/favorites, /api/saved-searches, /api/notifications
- GET /api/audit, /health, /docs

## Beperkingen

- Geen live scraping.
- DEMO-comparables zijn **geen** echte marktprijzen.
- ARV zonder echte comparables = onvoldoende gegevens.
- Aankoopkosten zijn indicatief (geen fiscaal advies).

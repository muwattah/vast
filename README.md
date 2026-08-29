# Antwerp Property Investor

**DIY Renovation Investment Platform for Antwerp**

A full-stack application that helps real-estate investors find, filter and score renovation properties in Antwerp (postcodes 2000–2660) with a focus on projects that can be largely executed as DIY.

## Important Legal & Technical Notes

- Live scraping of Immoweb, Zimmo, Immovlan and Biddit is **disabled by default**.
- These sites generally prohibit automated scraping in their Terms of Service and deploy anti-bot measures.
- The application ships with **clearly marked demo data** based on real market patterns so the full pipeline (database → scoring → API → dashboard) can be demonstrated and developed.
- To use real data you must obtain permission, use official APIs/partners, or import data manually / via allowed channels.
- Never put API keys in the frontend.

## Architecture

```
project/
├── frontend/          # Dashboard (HTML/JS)
├── backend/
│   ├── api/           # FastAPI routers
│   ├── scraper/       # Modular scrapers (stubs)
│   ├── ai/            # Scoring & analysis
│   ├── database/      # SQLAlchemy setup
│   ├── models/        # Property, Favorite, ...
│   └── services/      # Seed, demo, ...
├── .env.example
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Backend

```bash
cd /path/to/vast
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env if you have OPENAI_API_KEY or GROK_API_KEY

# Start API (from project root)
export PYTHONPATH=.
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs for interactive API docs.

### 2. Frontend

```bash
cd frontend
python -m http.server 3000
```

Open http://localhost:3000

### 3. What you should see

- Stats bar (total properties, DIY projects, high scores, avg €/m²)
- Filterable table of properties sorted by Investment Score
- Detail view with financial breakdown and analysis
- Favorites endpoints
- “Nu Vernieuwen” button (reports that live scrapers are disabled)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/properties | List with filters & sorting |
| GET | /api/properties/{id} | Detail |
| GET | /api/stats | Dashboard statistics |
| GET | /api/favorites | List favorites |
| POST | /api/favorites/{id} | Add favorite |
| DELETE | /api/favorites/{id} | Remove favorite |
| POST | /api/scrape | Trigger refresh (disabled by default) |

## Scoring Logic

Investment Score (configurable weights):

- 30% Margin potential
- 25% Purchase price attractiveness (€/m²)
- 20% Renovation potential (EPC E/F, “te renoveren” flags)
- 15% DIY suitability
- 10% Location

## Disclaimer

All cost, value and profit figures are **indicative estimates only**. They do not constitute financial, legal or investment advice.

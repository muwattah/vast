# Deployment

## SQLite (dev)
DATABASE_URL=sqlite:///./data/antwerp_properties.db

## PostgreSQL (prod)
docker compose up --build
# uses postgresql://vast:vast@db:5432/vast

Set SECRET_KEY in production.
Alembic available via alembic.ini for schema migrations.

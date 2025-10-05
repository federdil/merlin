# Merlin MVP Roadmap

This roadmap outlines the next steps to turn the current MVP into a reliable, demo-ready product and to package it for easy use by others.

Legend: ✅ Done · 🚧 Next · 💡 Optional/Nice-to-have

## What’s Done (MVP baseline) ✅
- ✅ Environment & deps: venv, updated `requirements.txt`, `.env.example`
- ✅ Database & vectors: pgvector enabled; tables and idempotent migrations; IVFFlat index
- ✅ Embeddings: `sentence-transformers` all-MiniLM-L6-v2 (384d)
- ✅ API endpoints (FastAPI):
  - `POST /add_note` (URL/text ingestion, embeddings, summarization/tags)
  - `GET /search` (semantic vector search with `top_k`)
  - `GET /notes/{id}` (detail)
  - `GET /similar/{id}` (nearest neighbors)
  - CORS for dev
- ✅ URL fetcher: `trafilatura` v2 (plain-text) with title fallback
- ✅ LLM integration: Anthropic (haiku models you have access to) with strict JSON parsing & local fallback
- ✅ Data hygiene: tags normalized to `List[str]`
- ✅ Streamlit UI: Ingest, Search, Settings tabs; cards/grid, tag chips, spinners

## Goals
- Solid ingestion (URL/text) with consistent titles, summaries, and tags
- Fast semantic search and high-quality “similar notes”
- Clean, pleasant UI for demoing value quickly
- Simple deployment so others can run it locally or via Docker

## Phase 1 — Quality & UX polish 🚧
- 🚧 URL/title quality: use metadata (`og:title`, `<title>`) and readability for better titles
- 🚧 Content handling: truncate/chunk very long content before embedding; basic language detection
- 🚧 Error handling: clearer messages for fetch/LLM failures; UI toasts
- 🚧 UI tweaks: stable card heights, smarter text truncation; (💡) note detail modal

## Phase 2 — Relevance & explainability 🚧
- 🚧 Hybrid search: optionally filter vector results by keyword/entity when query is a proper noun
- 🚧 Entity-aware tagging: extract named entities and add as tags; clickable chips for filtering
- 💡 Re-ranking: LLM re-rank top_k; show brief “Why this result”

## Phase 3 — Data & testing 🚧
- 🚧 Seeding: script to ingest 10–20 diverse articles for demos
- 🚧 Tests: unit (CRUD, embedding size, normalizers, fetcher) and integration (POST/GET with mocked LLM)
- 💡 Observability: request latency and LLM token usage

## Phase 4 — Ops & packaging 🚧
- 🚧 Docker: docker-compose for Postgres+pgvector, API, and UI
- 🚧 Config: centralized env (.env) for `DATABASE_URL`, `ANTHROPIC_API_KEY`, `API_URL`
- 🚧 Docs: expand README with quick start and troubleshooting

---

## Acceptance criteria for MVP demo
- Ingest URL/pasted text → title, summary, tags, and 3+ similar notes
- Search returns relevant notes quickly (~300ms on dev DB)
- URL-only ingestion reliable for mainstream news/blogs
- LLM on/off switch shows clear improvement when enabled

---

## Deployment instructions (standalone)

Below are two options: Local + Docker. Choose one.

### Option A: Local (venv)
1) Prerequisites
- Python 3.10+
- PostgreSQL 14+ with pgvector extension

2) Setup
```bash
# clone and enter repo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# environment
cp .env.example .env
# edit .env to set DATABASE_URL and (optionally) ANTHROPIC_API_KEY

# bootstrap DB (creates tables, enables pgvector, ensures index)
python -m db.create_tables
```

3) Run backend API
```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)  # or export variables manually
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

4) Run Streamlit UI
```bash
source .venv/bin/activate
API_URL="http://127.0.0.1:8002" streamlit run app/streamlit_app.py
```

5) Use
- Open the Streamlit URL printed in the terminal (usually http://localhost:8501)
- In Settings tab, confirm API URL if different

### Option B: Docker (recommended for sharing)
1) Create a `.env` file at repo root
```env
POSTGRES_USER=merlin
POSTGRES_PASSWORD=merlin
POSTGRES_DB=curator
DATABASE_URL=postgresql://merlin:merlin@db:5432/curator
ANTHROPIC_API_KEY=your_key_here  # optional; omit to use local fallback
API_URL=http://api:8002
```

2) Create a `docker-compose.yml` (outline)
```yaml
version: "3.9"
services:
  db:
    image: ankane/pgvector
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER"]
      interval: 5s
      timeout: 5s
      retries: 20

  api:
    build: .
    command: bash -lc "python -m db.create_tables && uvicorn app.main:app --host 0.0.0.0 --port 8002"
    environment:
      DATABASE_URL: ${DATABASE_URL}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8002:8002"

  ui:
    build: .
    command: bash -lc "streamlit run app/streamlit_app.py"
    environment:
      API_URL: ${API_URL}
    ports:
      - "8501:8501"
    depends_on:
      - api
```

3) Dockerfile (outline)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

4) Up the stack
```bash
docker compose up --build
```

5) Use
- UI at http://localhost:8501
- API at http://localhost:8002/docs

### Notes
- Without `ANTHROPIC_API_KEY`, the system uses local fallback summarization/tagging.
- For production, disable `--reload`, lock dependencies, and restrict CORS in `app/main.py`.

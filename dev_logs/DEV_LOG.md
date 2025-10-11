# Merlin – Development Log (MVP Phase 1)

Date: 2025-10-05

## Overview
Built an end-to-end MVP for Merlin, a personal knowledge curator: ingest (URL/text), summarize + tag (LLM with fallback), embed, store vectors in Postgres/pgvector, semantic search, similar-notes discovery, and a polished Streamlit UI.

## Environment & Dependencies
- Added `.env.example` with `DATABASE_URL`, `ANTHROPIC_API_KEY`.
- Created Python venv and installed dependencies.
- requirements updated: FastAPI/Starlette, Uvicorn, SQLAlchemy, psycopg2-binary, python-dotenv, anthropic, sentence-transformers, pgvector, trafilatura, faiss-cpu, streamlit, requests.

## Database & Vectors
- Enabled pgvector extension and created tables via `db/create_tables.py`.
- Model: `notes` with `title`, `content`, `summary`, `tags (VARCHAR[])`, `embedding (vector(384))`, `created_at`.
- Idempotent migrations: ensure columns exist; convert legacy TEXT tags to VARCHAR[]; ensure IVFFlat index:
  - `CREATE INDEX notes_embedding_idx ON notes USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);`

## Embeddings
- Using `sentence-transformers` `all-MiniLM-L6-v2` (384 dims) for content/query embeddings.

## API (FastAPI)
- `POST /add_note`:
  - Accepts `url` or `content` (+ optional `title`).
  - Fetches article text via `trafilatura` when `url` provided.
  - Summarizes + tags via Anthropic; added robust JSON parsing and local fallback.
  - Embeds and stores note with pgvector.
- `GET /search?query=&top_k=`: vector search using pgvector cosine distance.
- `GET /notes/{id}`: returns full note (title, summary, tags, content, timestamps).
- `GET /similar/{id}?top_k=`: nearest neighbors using stored embedding; excludes self.
- CORS enabled for dev.

## LLM Integration
- Anthropic client integrated with resilient parsing and logging.
- Chosen models based on account access:
  - Primary: `claude-3-5-haiku-20241022`
  - Fallback: `claude-3-haiku-20240307`
- Local fallback implemented (extractive summary + naive keyword tags) when API fails or JSON cannot be parsed.

## URL Fetching
- `trafilatura` v2-compatible fetcher using plain-text extraction.
- Title fallback to content snippet when meta title unavailable.

## Data Hygiene
- Unified tag handling: API normalizes tags to `List[str]` even if DB had legacy formats.

## Streamlit UI (MVP)
- Three tabs: Ingest, Search, Settings.
- Ingest:
  - URL/text input, optional title, LLM toggle, similar-notes count.
  - On success: card with title, summary, tags, note id.
  - Similar notes rendered as a responsive grid of cards (up to 3 per row), each showing title, summary, tag chips, and note id.
- Search:
  - Query + top_k; result cards with summaries and tags.
- Settings:
  - API URL configurable from within the app.
- Styling:
  - Hero header, custom CSS, card components, readable tag chips, spinners, and improved layout.

## Operational Notes
- Typical run commands:
  - API: `uvicorn app.main:app --reload --port 8002`
  - Streamlit: `API_URL=http://127.0.0.1:8002 streamlit run app/streamlit_app.py`
- Environment:
  - Ensure `DATABASE_URL` and `ANTHROPIC_API_KEY` are exported in the API process shell.

## Known Issues / Next Steps
- Title extraction: consider `readability-lxml`/metadata for better titles.
- Long content: chunk or truncate before embedding for quality/perf.
- Hybrid search: combine vector search with lightweight keyword filter for proper nouns.
- Entity-aware tagging: extract named entities during ingestion to enrich tags.
- Tests: add unit (CRUD, embedding size, normalizers) + integration (POST/GET with mocked LLM).
- Docker: add `docker-compose.yml` for Postgres with pgvector and a simple app stack.
- Observability: basic request latency logs and LLM usage metrics.

## Changelog Highlights
- db: schema creation + migrations; pgvector index; tags normalization.
- app: endpoints for ingest, search, note detail, similar; CORS.
- embeddings: HuggingFace ST model; deterministic embedding pipeline.
- llm: Anthropic integration with strict JSON parsing and fallbacks; model selection aligned to account.
- fetcher: trafilatura v2 extraction.
- streamlit: redesigned UI with cards, grid layout, settings tab, and UX polish.

---

# Major Update - README Documentation Overhaul

Date: 2025-10-11

## Overview
Comprehensive update to README.md documentation to reflect the current v2.0 Strands Agents architecture and technical stack. The documentation now accurately represents the evolved system architecture and provides complete setup instructions.

## Documentation Changes

### README.md Major Updates
- **Version Update**: Changed from "Phase 1 MVP" to "v2.0" to reflect current state
- **Architecture Description**: Updated to highlight intelligent agent routing capabilities
- **Technical Stack Table**: Completely refreshed with current technologies:
  - Strands Agents for agent orchestration
  - Claude 3.5 Haiku for AI reasoning
  - sentence-transformers for embeddings
  - trafilatura for content extraction
  - pytest & httpx for testing
  - YAML for configuration

### New Sections Added
- **Architecture Diagram**: Comprehensive file structure showing agent-based organization
- **Agent System Documentation**: Detailed descriptions of Router, Ingestion, Query, and Summarization agents
- **Setup Instructions**: Updated with current startup script (`start_merlin.py`) and correct port numbers
- **API Endpoints**: Current unified `/api/v1/process` endpoint documentation
- **Usage Examples**: Current curl commands and testing instructions
- **Configuration**: YAML configuration examples from `strands_config.yaml`

### Technical Accuracy Verification
- ✅ Claude model version: `claude-3-5-haiku-20241022`
- ✅ Embedding model: `all-MiniLM-L6-v2` (384 dimensions)
- ✅ API port: 8002
- ✅ Streamlit port: 8501
- ✅ API endpoints: `/api/v1/process`
- ✅ All dependencies match `requirements.txt`

## Key Improvements
- **Comprehensive Coverage**: Documentation now covers all aspects of the v2.0 system
- **Accurate Technical Details**: All specifications verified against current codebase
- **User-Friendly Setup**: Clear step-by-step instructions for new users
- **Developer Documentation**: Complete API reference and configuration guide
- **Architecture Clarity**: Visual representation of the agent-based system structure

## Files Modified
- `README.md`: Complete overhaul with v2.0 documentation
- `dev_logs/DEV_LOG.md`: Added today's update entry

## Impact
- New users can now easily understand and set up the system
- Technical documentation accurately reflects the current Strands Agents architecture
- Setup process is streamlined with clear instructions
- API usage is well-documented with examples

## Next Steps
- Push updated documentation to GitHub repository
- Verify all links and examples work correctly
- Consider adding video tutorials for complex setup scenarios

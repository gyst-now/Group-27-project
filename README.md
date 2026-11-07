# University Catalog Advisor

Public read-only Q&A over selected official UIUC 2026–27 CS, MATH, and Computer Science BS catalog pages.

**Live:** https://uiuc-catalog-advisor-gyst-now.vercel.app/ — connected to the existing Supabase project with 314 indexed chunks. Next.js/TypeScript frontend, Python 3.14 FastAPI, LangGraph/LangChain, OpenAI embeddings and Supabase pgvector. Independent educational prototype; not an official advising service.

## Local setup

Install Python 3.14 and Node 24. From the repository root:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell alternative: .venv\Scripts\Activate.ps1
pip install -r requirements.lock.txt
cp .env.example .env
```

Windows PowerShell: use `Copy-Item .env.example .env`. Populate the server-side OpenAI key, existing Supabase URL/secret key, and a random IP_HASH_SALT in `.env`. Do not paste secrets into chat or commit them. Model defaults to configurable `gpt-4.1-mini`; embedding dimensions are fixed at 1536.

Before applying SQL, inspect the existing project using `supabase/preflight.sql`. Confirm no app-object collisions, extension location and existing migration history. The migration passed disposable PGlite + pgvector integration tests (`npm ci --prefix tests && npm run --prefix tests test:database`). Inspect the hosted project before applying it. Apply `supabase/migrations/0001_catalog_rag.sql` through Supabase migrations. It creates only distinct `catalog_*` objects. Never reset the existing database. The migration intentionally fails on collisions rather than silently adopting incompatible tables.

```bash
python -m scripts.ingest_catalog --catalog-year 2026-27 --dry-run
python -m scripts.ingest_catalog --catalog-year 2026-27
python -m uvicorn api.index:app --reload --port 8000
```

In another terminal:

```bash
cd web
npm ci
# Create web/.env.local: NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000. Health: http://localhost:8000/api/health. Health means process liveness, not database readiness. Public chat fails closed with 503 if configuration, database, or budget service is unavailable.

Optional local Streamlit interface: `pip install streamlit`, then `streamlit run app.py`. It calls the same running API. It is not deployed to Vercel.

## Vercel: two projects

1. API project: repository root; framework Other. Root `vercel.json` builds `api/index.py` with the Python runtime; `.python-version` selects 3.14. Set server-only environment variables from `.env.example`. ALLOWED_ORIGINS must contain the exact frontend production origin; no trailing slash.
2. Frontend project: root directory `web`, framework Next.js, Node 24. Set NEXT_PUBLIC_API_BASE_URL to the API production origin, then build/deploy. Only this public URL belongs in the browser bundle.
3. Set both projects' production access to public as specified. Test health, supported query, unsupported query, and allowed-origin CORS on the final production domains. Preview domains are not automatically permitted.

The project names created during implementation are `uiuc-catalog-api` and `uiuc-catalog-advisor` under GYST-Now. Actual URLs and status belong in docs/EVALUATION.md.

## Data and costs

Only three allowlisted URLs are fetched. Pages must establish the 2026–27 edition. Course-block extraction retains prerequisites; long records use 1000-character chunks with 120 overlap and repeated identity. Source replacement is atomic after all embeddings for that source succeed. Deterministic IDs prevent duplicate rows on repeated indexing. Partial-source failure does not clear other sources. Ingestion run records do not contain private transcripts.

RLS blocks direct anon/authenticated access, including RPC execution. Backend uses the service-role key only on the server. Distributed SQL rate limiting admits at most 10 requests/IP/minute and 200 total/day by default, bounded to a maximum 1000/day. All requests consume budget before OpenAI calls, including provider failures. This limits request volume, not an exact dollar amount: configure provider budgets/alerts and Vercel spend controls. Model and hosting usage can incur charges. Question size, retrieved context and model output are bounded; no paid reranker or agent loop.

Logs record request ID, status, latency, source count or exception class; no question/answer transcripts. IPs use a salted HMAC; database counters expire and are removed on future requests. Avoid enabling external tracing without reviewing its transcript retention.

## Checks and evaluation

```bash
python -m pytest -q
npm --prefix web run build
python -m evals.run_evals --base-url https://YOUR-API-DOMAIN
```

`evals/questions.jsonl` contains 15 cases. Raw CSV records actual responses and latency. Grade faithfulness/citation support/no-answer correctness manually; blank fields mean not reviewed. Returned source coverage is not retrieval hit@5. Acceptance goals remain unmeasured until a configured corpus and model are exercised. See docs/EVALUATION.md, PROJECT_REPORT.md and DEMO_SCRIPT.md.

# Build handoff — connected deployment

## Implemented and deployed
Python 3.14 FastAPI backend; bounded LangGraph evidence workflow using LangChain OpenAI; official-source ingestion and dry run; Supabase pgvector search, atomic replacement, RLS and distributed budgets; Next.js UI; local Streamlit fallback; 15-case evaluation harness; report and demo script.

- Web: https://uiuc-catalog-advisor-gyst-now.vercel.app/
- API health: https://uiuc-catalog-api-gyst-now.vercel.app/api/health
- Vercel team: GYST-Now; projects uiuc-catalog-api and uiuc-catalog-advisor.
- Existing Supabase: group project, ijjjherxqfmlypxomxur; connection Group 27 Supabase.
- All required production environment settings are saved. The backend supports modern SUPABASE_SECRET_KEY and legacy SUPABASE_SERVICE_ROLE_KEY. Secret values were not read into the conversation.
- The app now returns real cited answers and rejects unsupported live-seat questions. Browser verified CS 225 prerequisite answer and seat-availability rejection.
- Two completed ingestion runs: 3 sources, 314 chunks each; resulting row counts unchanged, confirming repeat-ingestion idempotency on hosted Supabase.
- Temporary administrator ingestion build hook removed in the final deployment. Public endpoints do not perform ingestion.
- Retrieval returns five passages with source metadata for evaluation. Citations are supplied from validated source metadata.

## Validation
19 pytest tests passed. Next.js build/TypeScript passed. Disposable PostgreSQL + pgvector integration checks passed. Hosted migration and RLS/privilege checks passed. See EVALUATION.md for live evaluation results and SUPABASE_SETUP.md for preflight and existing advisory findings.

## Remaining submission work
- Repository destination is now https://github.com/gyst-now/Group-27-project . The gyst-now GitHub connection successfully created codex/catalog-rag-mvp; the implementation is supplied there as a reviewable pull request. Earlier permission errors applied to the previous connection/repository.
- Vercel projects were deployed from source files and are not Git-linked. A GitHub push will not auto-deploy until linked.
- Google Doc creation and demo recording remain separate submission tasks. Use PROJECT_REPORT.md and DEMO_SCRIPT.md.
- Human review of semantic evaluation is still required before claiming human-reviewed faithfulness/citation scores.

## Local setup
```bash
python -m venv .venv
# Activate .venv for your operating system.
pip install -r requirements.lock.txt
# Copy .env.example to .env and configure credentials securely.
python -m scripts.ingest_catalog --dry-run
# Hosted migration is already installed. Normal ingestion is an explicit admin action:
python -m scripts.ingest_catalog
python -m uvicorn api.index:app --port 8000
```
Second terminal: `cd web`, `npm ci`, set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in web/.env.local, `npm run dev`.

## Files
- Configuration: .env.example, .gitignore, .python-version, pyproject.toml, requirements*.txt, vercel.json.
- API/local UI: api/index.py, app.py.
- Backend: src/config.py, catalog.py, vectorstore.py, graph.py, schemas.py, prompts.py.
- Ingestion: scripts/ingest_catalog.py.
- Database: supabase/preflight.sql, supabase/migrations/0001_catalog_rag.sql.
- Frontend: web/app/page.tsx, layout.tsx, globals.css; package.json, package-lock.json, tsconfig.json, next-env.d.ts.
- Tests: tests/test_catalog.py, test_graph.py, test_api.py, test_config.py, test_sql_contract.py, check_database.mjs and package manifests.
- Evaluation: evals/questions.jsonl, run_evals.py, original diagnostic results and configured-results files.
- Documentation: README.md, docs/CODEX_SPEC.md, PROJECT_REPORT.md, EVALUATION.md, DEMO_SCRIPT.md, BUILD_STATUS.md, SUPABASE_SETUP.md.

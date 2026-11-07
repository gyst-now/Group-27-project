# Demo script — target 4:55

- 0:00–0:30: Problem: selected UIUC course and degree catalog Q&A, independent prototype, no private records.
- 0:30–1:15: Explain Next.js → FastAPI → bounded LangGraph → Supabase pgvector → cited answer. Three official sources, edition-checked.
- 1:15–2:15: Show ingestion dry run, source/chunk counts, SQL RLS and search RPC. Explain deterministic IDs and atomic per-source replacement. Explain how Codex was used; show tests.
- 2:15–3:10: With a configured corpus, ask “What is CS 124?” and “What prerequisites are listed for CS 225?” Open citation and retrieved evidence; compare with source.
- 3:10–3:35: Ask “Does CS 225 have open seats next semester?” Show honest limitation. If deployment is unconfigured, clearly show service unavailability rather than presenting it as a RAG rejection.
- 3:35–4:25: Open actual evaluation CSV. Explain human faithfulness and citation review, measured latency, errors, and unmeasured fields. Never present goals as scores.
- 4:25–4:55: Discuss corpus limits, next improvements, repo and verified deployment URLs. State any remaining blockers.

Record only after a configured live run is available for the supported-answer demonstration. Do not display credentials or environment files.

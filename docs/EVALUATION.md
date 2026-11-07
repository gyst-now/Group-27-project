# Evaluation — 2026-11-06 America/Chicago

The configured deployment is now connected, indexed and answering questions. The initial diagnostic results below are historical; the configured run at the end supersedes its blocker status.

## Initial deployment diagnostic (historical)
- Frontend: https://uiuc-catalog-advisor-gyst-now.vercel.app/
- Python API: https://uiuc-catalog-api-gyst-now.vercel.app/api/health

Both deployments reached READY. Public, unauthenticated frontend rendering and question submission were checked in a browser. Public health returned 200 with the required JSON. Allowed-origin CORS preflight returned 200 and the exact frontend origin. Chat returned a redacted 503 because backend credentials/corpus are not configured. The browser displays a graceful service-unavailable message. This is an operational error, not a successful evidence rejection.

## Measured checks
| Check | Result |
|---|---|
| Python runtime | 3.14.9 installed; Vercel Python 3.14 executed health successfully |
| Python unit/API/graph tests | 14 passed (dependency deprecation warnings only) |
| Next.js production build and TypeScript | passed, Next.js 16.4.5 |
| Disposable SQL engine | PGlite 0.5.15 + pgvector 0.0.16; migration, insert/search/delete, repeated replacement, failed replacement rollback, edition filter, exact lookup, budget denial, anonymous table/RPC denial passed |
| Official-source dry run | 3 pages fetched, 314 chunks; 161 CS courses, 112 MATH courses; edition text verified |
| Existing Supabase | Connected account listed zero projects; no migration or indexing applied |
| GitHub push | Not performed: CLI lacks credentials; connector branch creation returned 403 |

To reproduce SQL tests: `npm ci --prefix tests && npm run --prefix tests test:database`. This tests embedded PostgreSQL + pgvector, not the user's hosted Supabase integration, and does not prove its existing extension layout or privileges.

## Fifteen-request deployment diagnostic run
All 15 documented cases were sent to the public API. The run overlapped the initial deployment repair: Q01–Q06 returned 500 due to missing Python dependencies; Q07–Q15 returned the corrected application's redacted 503 due to missing backend settings. Raw responses and timings are in evals/results.csv and results.summary.json.

- Requests: 15; errors: 15.
- Across **error requests**, p50 3700 ms; nearest-rank p95 17132 ms.
- Successful answer latency: **not measured**.
- Faithfulness, citation validity, retrieval hit@5, no-answer correctness: **not measured**.
- No acceptance-quality claim is established by this diagnostic run.

After configuration, run `python -m evals.run_evals --base-url https://uiuc-catalog-api-gyst-now.vercel.app --output evals/configured-results.csv`. Human reviewers must compare every substantive claim against its supporting excerpt. Score claim support, citation support and correct rejection separately. Returned citation URL coverage is not retrieval hit@5. Add a controlled retrieval evaluation against hand-annotated chunks for hit@5. Do not publish human grades without review.

## Observed failures and limitations
1. Vercel prioritized pyproject.toml over requirements.txt. Its first build omitted FastAPI and failed at import. Fixed by declaring runtime dependencies in pyproject.toml; redeployed and verified public health.
2. The Supabase connection returned no accessible projects. Existing-project inspection, migration and live ingestion remain blocked. No unrelated database was created or changed.
3. GitHub CLI could not authenticate and the connected integration denied branch creation with 403. Code is locally committed on codex/catalog-rag-mvp and supplied as an archive. No remote branch or PR exists.
4. Live semantic evaluation is blocked by absent database and OpenAI credentials. All raw diagnostic failures are retained; quality targets remain unmeasured.

## Initial acceptance status (historical)
Implemented and tested locally: source parsing/provenance, atomic source replacement, graph branches, citation-ID validation, API validation/errors, frontend, SQL search and access controls. Deployed: frontend and Python health/error paths. Pending: hosted Supabase migration, embedded corpus, repeated hosted ingestion, supported live answers, reviewed semantic evaluation, Google Doc creation and video recording. Public production credentials must be configured before the app can answer catalog questions.

## Configured live run (current)

The Group 27 Supabase connection now authorizes the intended existing project. The additive migration was applied after preflight; two complete ingestion runs each indexed 314 chunks from 3 sources, with 314 total rows after both runs (no duplicates). Details: SUPABASE_SETUP.md.

The public frontend and API now return real cited answers. Browser checks verified a CS 225 prerequisite answer with a clickable citation/evidence disclosure and an honest rejection of live-seat availability. Health returned 200, allowed-origin CORS returned 200, whitespace-only chat validation returned 422.

`evals/configured-results.csv` and `.summary.json` record the 15-question live run:

| Metric | Observed |
|---|---|
| HTTP successes | 15/15 |
| API errors | 0/15 |
| End-to-end p50 | 6,309 ms |
| End-to-end nearest-rank p95 | 9,513 ms |
| Source-URL retrieval hit@5 | 12/12 answerable cases (100%) |
| Clearly unsupported questions rejected | Q13 and Q14, 2/2 |
| Ambiguous question correctly clarified | Q15 initially failed; corrected with deterministic ambiguity guard |
| Human-reviewed faithfulness | not measured |
| Human-reviewed citation validity | not measured |

These timings include client/network overhead and are a small sequential sample, not a load test or a guarantee of sustained warmed p95. Source-URL hit@5 is a coarse page-level metric: it does not prove that the right course passage was retrieved or that every claim was supported. The conceptual linear-algebra failure below demonstrates that limitation.

### Actual semantic failures found during assistant review

1. Q04: CS 374's catalog prerequisite text says “One of CS 173, MATH 213; CS 225.” The initial generated description rewrote this into an OR across all three courses. The prompt now excludes unsolicited prerequisites and requires exact prerequisite quoting when requested. No prerequisite eligibility audit is implemented.
2. Q07: The initial linear-algebra topic answer included MATH 522 because linear algebra appears in its prerequisites. The prompt now distinguishes topics taught by a course from topics listed only as prerequisites.
3. Q15: A bare “225” question was answered as MATH 225 without identifying the intended subject. The graph now detects ambiguous bare course-number questions before embeddings/model invocation and explicitly asks for CS vs MATH.

The full original configured run remains unchanged. `evals/retest_failures.py` reruns only Q04, Q07 and Q15; responses are saved in `evals/retested-failures.json`. This targeted retest is separate from the baseline, and does not retroactively turn the original responses into passes. Human review of final semantics remains required.

Latest local checks: 18 pytest tests pass, including modern secret-key authentication, retrieval metadata and deterministic ambiguity handling. The prior Next.js production build and disposable database integration checks remain valid; no frontend or migration source changed during the semantic fixes.

### Targeted retest outcomes
Q04 now omits unsolicited prerequisites and its description is supported. Q15 now requests the subject before retrieval and returns insufficient_evidence. Both returned HTTP 200.

Q07 still listed MATH 522 after the prompt-only change, despite describing its linear algebra as a prerequisite. This failed retest is retained in retested-failures.json. The graph was then changed to exclude a topic-search hit when the explicitly requested topic phrase appears only after “Prerequisite:” and not in the course title/description. A deterministic regression test covers this distinction. This is a conservative lexical exclusion, not a calibrated general-purpose semantic reranker.

The final topic-filter retest returned HTTP 200 and listed only MATH 227, MATH 257, MATH 415 and MATH 416; MATH 522 was absent from both retrieved passages and answer. Raw response: evals/retested-topic-filter.json. All 19 local pytest tests pass. Final API deployment dpl_CqtSiP573ZFSbpAfQpDpT16oCKtX reached READY and retains the stable production alias. The observed failures, unsuccessful prompt-only retest and successful targeted fixes are all preserved.

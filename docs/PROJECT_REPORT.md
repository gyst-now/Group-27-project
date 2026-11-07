# University Catalog Advisor — project report

## Overview
A bounded retrieval workflow answers selected UIUC 2026–27 undergraduate catalog questions. It explains published information, and does not provide official advice, degree clearance, transfer equivalency or live registration data.

## Sources and pipeline
- https://catalog.illinois.edu/courses-of-instruction/cs/
- https://catalog.illinois.edu/courses-of-instruction/math/
- https://catalog.illinois.edu/undergraduate/engineering/computer-science-bs/

The ingestion command allowlists sources and validates edition text. BeautifulSoup extracts course records or content sections. Long text is split at 1000 characters with 120 overlap. Each chunk retains URL, edition, heading, optional course identifier and deterministic identity. Source HTML hash and timestamp are recorded. OpenAI text-embedding-3-small provides 1536-dimensional vectors. Supabase SQL provides cosine retrieval plus exact course-code matches. Replacement is atomic per source after embeddings complete.

## Workflow and prompts
LangGraph nodes: retrieve_catalog → assess_evidence → generate_grounded_answer OR insufficient_evidence. Assessment generates a structured candidate answer and selected evidence IDs in one LLM call; the answer node validates and attaches citations. This avoids a second synthesis call while retaining explicit routing. Source URLs are always supplied from server metadata. Unknown citation IDs invalidate the answer. The model determines semantic sufficiency; there is no uncalibrated similarity cutoff. This still requires human evaluation for claim-level support.

System prompt: src/prompts.py. Catalog text is untrusted data; only provided evidence may support answers. Missing/ambiguous information routes to a limitation response. A fixed no-evidence message is conservative and does not expose the model's unsupported proposed answer.

## Implementation iterations
The actual repository contained only a README and ignore file, despite the specification describing a prior prototype. Implementation therefore started from a clean baseline. Python 3.14 and dependencies were installed successfully. HTTP fetching in the build environment required an optional SOCKS transport dependency. Public access is bounded by transactional database counters, not process-local memory, to work across serverless instances.

## Evaluation and lessons
See EVALUATION.md for measured checks and remaining gaps. Automated unit tests exercise routing, citation-ID integrity, source allowlisting, edition rejection, API input validation, error redaction and budget denial. These do not establish model faithfulness. The existing Supabase project is now connected and populated; actual deployed evaluation responses are recorded separately from the initial diagnostic failures. Human semantic review remains a submission task.

## Limitations
Character splitting can separate complex degree-table context. Exact-code matches improve code lookup but conceptual recall and cross-page coverage need evaluation. There is no deterministic prerequisite audit. Citation presence and valid URLs do not prove claim-level faithfulness. Separate frontend and API deployments require explicit origin configuration. SQL migration passed disposable PGlite + pgvector checks; hosted Supabase preflight is still required before applying to the existing project.

## AI coding workflow
Codex read the supplied spec, inspected GitHub, implemented code and documentation, installed Python 3.14 dependencies, fetched source pages in dry-run mode and ran automated checks. Results are distinguished from proposed goals. This Markdown is ready to paste into a Google Doc; creation of a Google Doc and recording the demo remain separate submission steps.

## Live deployment outcome
The Group 27 Supabase connection now reaches the original class project. The additive migration and two ingestion runs completed; 314 chunks remain without duplication. Real public answers and negative-query behavior were verified. The 15-query baseline had no HTTP errors, page-level source hit@5 of 12/12, p50 6.309 seconds and p95 9.513 seconds. Review found ambiguity, prerequisite-logic and prerequisite-only topic errors. Targeted fixes and retests are preserved in EVALUATION.md. These observations do not replace human claim-level faithfulness review. Latest tests: 19 passed.

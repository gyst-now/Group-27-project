# Existing Supabase project setup

Connected account: Group 27 Supabase. Project: group project (`ijjjherxqfmlypxomxur`), PostgreSQL 17.11. The Primary connection has no accessible projects.

Preflight inspected tables, existing RLS policies, privileges, public functions, extensions and migration history. Existing class tables: meetings, tasks, decisions, resources, links, polls, team_members, allowed_members. No catalog-object collisions. pgvector was absent and installed in extensions (0.8.2). The catalog_rag migration added only catalog-specific tables, indexes and functions; existing class objects/data/policies were not modified.

Verification: all four catalog tables have RLS enabled; anon cannot SELECT catalog_chunks or execute catalog_take_budget. The service-role backend accesses only the catalog objects. Public visitors do not sign into Supabase or receive secret keys.

Two real administrator ingestion runs completed with 3 sources and 314 chunks each. The resulting table still has exactly 3 sources and 314 chunks: CS 176 chunks, MATH 114, CS BS 24. Provenance hashes and fetch timestamps are stored per source. Embeddings use text-embedding-3-small, 1536 dimensions.

Because production Secret values cannot be pulled locally, ingestion ran as a temporary Vercel administrator build command using the already-saved runtime credentials. The build ran the existing CLI twice; no HTTP ingestion endpoint was created. The following normal API deployment removed the temporary ingestion hook. Normal deployments and public chat do not ingest content.

## Existing advisory findings
Security advisories before and after the migration include existing SECURITY DEFINER functions and disabled leaked-password protection. These belong to the earlier application and were left unchanged:
- https://supabase.com/docs/guides/database/database-linter?lint=0028_anon_security_definer_function_executable
- https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable
- https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

The new catalog tables have RLS with no public policies intentionally, because this application permits only server-side service-role access. No-policy advisory: https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy . This is a deliberate deny-by-default arrangement.

A performance advisory notes a missing covering index on catalog_chunks.source_id. With 314 chunks this is a documented optimization opportunity, not a functional blocker. The HNSW and FTS indexes may be reported as unused while the small-corpus planner prefers sequential scans. No index was removed. Reference: https://supabase.com/docs/guides/database/database-linter?lint=0001_unindexed_foreign_keys .

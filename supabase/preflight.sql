-- Read-only checks before additive migration. Inspect results; do not execute migration blindly.
show server_version;
select extname,extversion,n.nspname as extension_schema from pg_extension e join pg_namespace n on n.oid=e.extnamespace;
select schemaname,tablename,rowsecurity from pg_tables where schemaname not in ('pg_catalog','information_schema');
select schemaname,tablename,policyname,roles,cmd from pg_policies;
select routine_schema,routine_name from information_schema.routines where routine_schema='public';
select grantee,table_schema,table_name,privilege_type from information_schema.table_privileges where table_schema='public';
-- Separately inspect Supabase migration history via its migration-list API.
-- Abort if catalog_* names collide, or vector is installed outside extensions.

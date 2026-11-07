from pathlib import Path
def test_sql_security_contract():
    sql=Path('supabase/migrations/0001_catalog_rag.sql').read_text()
    for table in ('catalog_sources','catalog_chunks','catalog_ingestion_runs','catalog_usage'):
        assert f'alter table public.{table} enable row level security' in sql
    assert 'from public,anon,authenticated' in sql
    assert 'pg_advisory_xact_lock' in sql
    assert '1-(c.embedding <=> query_embedding)' in sql
    assert 's.catalog_year=selected_catalog_year' in sql

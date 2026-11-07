begin;
create schema if not exists extensions;
create extension if not exists vector with schema extensions;
-- Preflight must verify vector is in extensions, and these object names are unused.
create table public.catalog_sources (
 id uuid primary key default gen_random_uuid(), source_url text not null, title text not null,
 catalog_year text not null, content_hash text, fetched_at timestamptz,
 updated_at timestamptz not null default now(), unique(source_url,catalog_year));
create table public.catalog_chunks (
 id text primary key, source_id uuid not null references public.catalog_sources(id) on delete cascade,
 catalog_year text not null, course_code text, heading text, content text not null,
 chunk_order integer not null, embedding extensions.vector(1536) not null,
 created_at timestamptz not null default now());
create index catalog_chunks_embedding_hnsw on public.catalog_chunks using hnsw (embedding extensions.vector_cosine_ops);
create index catalog_chunks_fts on public.catalog_chunks using gin(to_tsvector('english',content));
create table public.catalog_ingestion_runs (
 id uuid primary key default gen_random_uuid(), started_at timestamptz not null default now(),
 finished_at timestamptz, status text not null default 'running', fetched_sources int not null default 0,
 indexed_chunks int not null default 0, error_summary text);
create table public.catalog_usage (bucket text primary key, count integer not null, expires_at timestamptz not null);
alter table public.catalog_sources enable row level security;
alter table public.catalog_chunks enable row level security;
alter table public.catalog_ingestion_runs enable row level security;
alter table public.catalog_usage enable row level security;
revoke all on public.catalog_sources, public.catalog_chunks, public.catalog_ingestion_runs, public.catalog_usage from anon, authenticated;
grant all on public.catalog_sources, public.catalog_chunks, public.catalog_ingestion_runs, public.catalog_usage to service_role;

create function public.match_catalog_chunks(query_embedding extensions.vector(1536), match_count int, selected_catalog_year text)
returns table(id text, content text, course_code text, heading text, source_url text, similarity double precision)
language sql stable set search_path=public,extensions as $$
 select c.id,c.content,c.course_code,c.heading,s.source_url,1-(c.embedding <=> query_embedding)
 from catalog_chunks c join catalog_sources s on s.id=c.source_id
 where c.catalog_year=selected_catalog_year and s.catalog_year=selected_catalog_year
 order by c.embedding <=> query_embedding limit least(greatest(match_count,1),10)
$$;
create function public.catalog_exact_chunks(codes text[], selected_catalog_year text)
returns table(id text, content text, course_code text, heading text, source_url text, similarity double precision)
language sql stable set search_path=public as $$
 select c.id,c.content,c.course_code,c.heading,s.source_url,1.0::double precision
 from catalog_chunks c join catalog_sources s on s.id=c.source_id
 where c.course_code=any(codes) and c.catalog_year=selected_catalog_year and s.catalog_year=selected_catalog_year
 order by c.course_code,c.chunk_order limit 10
$$;
-- Atomic replacement: embeddings are computed before this transaction; failed insertion rolls back deletion.
create function public.catalog_replace_source(source_url_arg text, hash_arg text, year_arg text, chunks_arg jsonb)
returns int language plpgsql set search_path=public,extensions as $$
declare sid uuid; n int;
begin
 if jsonb_array_length(chunks_arg)=0 then raise exception 'Empty source rejected'; end if;
 insert into catalog_sources(source_url,title,catalog_year,content_hash,fetched_at)
 values(source_url_arg,source_url_arg,year_arg,hash_arg,now())
 on conflict(source_url,catalog_year) do update set content_hash=excluded.content_hash,fetched_at=now(),updated_at=now()
 returning id into sid;
 delete from catalog_chunks where source_id=sid;
 insert into catalog_chunks(id,source_id,catalog_year,course_code,heading,content,chunk_order,embedding)
 select r.id,sid,year_arg,r.course_code,r.heading,r.content,r.chunk_order,r.embedding::extensions.vector
 from jsonb_to_recordset(chunks_arg) as r(id text,course_code text,heading text,content text,chunk_order int,embedding text);
 get diagnostics n=row_count;
 return n;
end $$;
-- Global cap and per-IP minute counter use transaction locks, across all serverless instances.
create function public.catalog_take_budget(ip_hash text, minute_limit int, daily_limit int)
returns boolean language plpgsql set search_path=public as $$
declare daykey text := 'day:'||to_char(now() at time zone 'UTC','YYYYMMDD');
 minkey text := 'ip:'||ip_hash||':'||to_char(now() at time zone 'UTC','YYYYMMDDHH24MI');
 current_count int;
begin
 perform pg_advisory_xact_lock(hashtextextended('catalog-budget',0));
 delete from catalog_usage where expires_at < now();
 select count into current_count from catalog_usage where bucket=daykey;
 if coalesce(current_count,0)>=least(greatest(daily_limit,1),1000) then return false; end if;
 select count into current_count from catalog_usage where bucket=minkey;
 if coalesce(current_count,0)>=least(greatest(minute_limit,1),30) then return false; end if;
 insert into catalog_usage values(daykey,1,now()+interval '2 days') on conflict(bucket) do update set count=catalog_usage.count+1;
 insert into catalog_usage values(minkey,1,now()+interval '2 minutes') on conflict(bucket) do update set count=catalog_usage.count+1;
 return true;
end $$;
revoke all on function public.match_catalog_chunks(extensions.vector,int,text), public.catalog_exact_chunks(text[],text), public.catalog_replace_source(text,text,text,jsonb), public.catalog_take_budget(text,int,int) from public,anon,authenticated;
grant execute on function public.match_catalog_chunks(extensions.vector,int,text), public.catalog_exact_chunks(text[],text), public.catalog_replace_source(text,text,text,jsonb), public.catalog_take_budget(text,int,int) to service_role;
commit;

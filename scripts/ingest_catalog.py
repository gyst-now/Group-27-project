import argparse
import hashlib
import json
import time
from pathlib import Path
from src.catalog import fetch_source, parse_html
from src.config import Settings, URLS, YEAR
from src.vectorstore import VectorStore
from langchain_openai import OpenAIEmbeddings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog-year', choices=[YEAR], default=YEAR)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    pages = []
    for url in URLS:
        html = fetch_source(url)
        chunks = parse_html(html, url)
        pages.append((url, html, chunks))
        print(json.dumps({'source': url, 'chunks': len(chunks), 'courses': len({c['course_code'] for c in chunks if c['course_code']}), 'sample': chunks[0]['content'][:250]}))
        time.sleep(0.5)
    print(json.dumps({'sources': len(pages), 'chunks': sum(len(p[2]) for p in pages), 'estimated_tokens_upper_approx': sum(len(c['content']) for _,_,cs in pages for c in cs)//3}))
    if args.dry_run:
        return
    settings = Settings.load()
    store = VectorStore(settings)
    embedder = OpenAIEmbeddings(model='text-embedding-3-small', dimensions=1536, api_key=settings.openai_key, request_timeout=30, max_retries=1)
    response = store.client.post('catalog_ingestion_runs', json={}, headers={'Prefer': 'return=representation'})
    response.raise_for_status()
    run_id = response.json()[0]['id']
    total = 0
    completed = 0
    try:
        for url, html, chunks in pages:
            vectors = embedder.embed_documents([c['content'] for c in chunks])
            for chunk, vector in zip(chunks, vectors, strict=True):
                chunk['embedding'] = json.dumps(vector)
            total += store.replace_source(url, hashlib.sha256(html.encode()).hexdigest(), chunks)
            completed += 1
        status = {'status': 'completed'}
    except Exception as exc:
        status = {'status': 'failed', 'error_summary': type(exc).__name__}
        raise
    finally:
        from datetime import datetime, timezone
        status.update(finished_at=datetime.now(timezone.utc).isoformat(), fetched_sources=completed, indexed_chunks=total)
        r = store.client.patch('catalog_ingestion_runs', params={'id': 'eq.'+run_id}, json=status)
        r.raise_for_status()
    print(json.dumps({'indexed_chunks': total, 'sources': completed}))

if __name__ == '__main__':
    main()

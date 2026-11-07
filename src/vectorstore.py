import httpx
from src.config import Settings, YEAR

class VectorStore:
    def __init__(self, settings: Settings):
        headers = {'apikey': settings.supabase_key}
        # New opaque secret keys authenticate through apikey, not a JWT bearer header.
        if not settings.supabase_key.startswith('sb_secret_'):
            headers['Authorization'] = f'Bearer {settings.supabase_key}'
        self.client = httpx.Client(base_url=settings.supabase_url.rstrip('/') + '/rest/v1/',
            headers=headers, timeout=20)

    def rpc(self, name: str, payload: dict):
        response = self.client.post('rpc/' + name, json=payload)
        response.raise_for_status()
        return response.json()

    def search(self, embedding: list[float], question: str) -> list[dict]:
        import re
        codes = re.findall(r'\b(?:CS|MATH)\s*\d{3}\b', question.upper())
        codes = [re.sub(r'\s*(\d)', r' \1', c, count=1) for c in codes]
        exact = self.rpc('catalog_exact_chunks', {'codes': codes, 'selected_catalog_year': YEAR}) if codes else []
        semantic = self.rpc('match_catalog_chunks', {'query_embedding': embedding, 'match_count': 5, 'selected_catalog_year': YEAR})
        merged = {r['id']: r for r in exact + semantic}
        return list(merged.values())[:5]

    def replace_source(self, url: str, html_hash: str, chunks: list[dict]):
        return self.rpc('catalog_replace_source', {'source_url_arg': url, 'hash_arg': html_hash,
                       'year_arg': YEAR, 'chunks_arg': chunks})

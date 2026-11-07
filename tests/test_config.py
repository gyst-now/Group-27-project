from src.config import Settings
from src.vectorstore import VectorStore

def test_modern_secret_header_and_precedence(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', 'https://example.supabase.co')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-openai')
    monkeypatch.setenv('SUPABASE_SECRET_KEY', 'sb_secret_test')
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY', 'legacy-test')
    settings = Settings.load()
    store = VectorStore(settings)
    assert store.client.headers['apikey'] == 'sb_secret_test'
    assert 'Authorization' not in store.client.headers
    store.client.close()

def test_legacy_fallback(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', 'https://example.supabase.co')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-openai')
    monkeypatch.delenv('SUPABASE_SECRET_KEY', raising=False)
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY', 'legacy-test')
    store = VectorStore(Settings.load())
    assert store.client.headers['Authorization'] == 'Bearer legacy-test'
    store.client.close()

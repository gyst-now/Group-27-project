from fastapi.testclient import TestClient
import api.index as api
client=TestClient(api.app)
def test_health(): assert client.get('/api/health').json()['catalog_year']=='2026-27'
def test_validation():
    for body in ({'question':' '},{'question':'x'*1001},{'question':'test','catalog_year':'2025-26'}):
        assert client.post('/api/chat',json=body).status_code==422
def test_fail_closed(monkeypatch):
    monkeypatch.setattr(api,'take_budget',lambda r:False)
    assert client.post('/api/chat',json={'question':'hello'}).status_code==429
def test_redacted_error(monkeypatch):
    def bad(r): raise RuntimeError('secret-do-not-expose')
    monkeypatch.setattr(api,'take_budget',bad)
    response=client.post('/api/chat',json={'question':'hello'})
    assert response.status_code==503
    assert 'secret-do-not-expose' not in response.text
def test_success_preserves_retrieval_metadata(monkeypatch):
    class Graph:
        def invoke(self, state):
            return {'answer':'Supported answer', 'status':'answered', 'citations':[],
                    'passages':[{'id':'chunk-1','source_url':'https://catalog.illinois.edu/courses-of-instruction/cs/','course_code':'CS 124','similarity':0.8}]}
    monkeypatch.setattr(api,'take_budget',lambda request:True)
    monkeypatch.setattr(api,'get_graph',lambda:Graph())
    response=client.post('/api/chat',json={'question':'What is CS 124?'})
    assert response.status_code==200
    data=response.json()
    assert data['retrieved_sources'][0]['id']=='chunk-1'
    assert data['retrieved_sources'][0]['similarity']==0.8
    assert data['request_id']

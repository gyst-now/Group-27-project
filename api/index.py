import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from functools import lru_cache
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from src.config import Settings, YEAR
from src.graph import production_graph
from src.schemas import ChatRequest, ChatResponse
from src.vectorstore import VectorStore

app = FastAPI(title='University Catalog Advisor', docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(','), allow_methods=['POST','GET'], allow_headers=['Content-Type'])
logger = logging.getLogger('catalog')

@lru_cache
def get_graph():
    return production_graph()

@lru_cache
def get_store():
    return VectorStore(Settings.load())

def take_budget(request: Request):
    salt = os.getenv('IP_HASH_SALT')
    if not salt:
        raise RuntimeError('Configure IP_HASH_SALT')
    # Trust Vercel's platform-controlled header only on Vercel; never arbitrary X-Forwarded-For.
    ip = request.headers.get('x-vercel-forwarded-for', '') if os.getenv('VERCEL') else (request.client.host if request.client else 'unknown')
    digest = hmac.new(salt.encode(), ip.encode(), hashlib.sha256).hexdigest()
    return get_store().rpc('catalog_take_budget', {'ip_hash': digest, 'minute_limit': int(os.getenv('REQUESTS_PER_MINUTE', '10')), 'daily_limit': int(os.getenv('DAILY_REQUEST_CAP', '200'))})

@app.get('/api/health')
def health():
    return {'status': 'ok', 'catalog_year': YEAR, 'vector_backend': 'supabase_pgvector'}

@app.post('/api/chat', response_model=ChatResponse)
def chat(body: ChatRequest, request: Request):
    start = time.perf_counter()
    request_id = str(uuid.uuid4())
    try:
        if not take_budget(request):
            raise HTTPException(429, 'Request limit reached. Please try later.')
        result = get_graph().invoke({'question': body.question})
        response = ChatResponse(answer=result['answer'], status=result['status'], citations=result['citations'],
            request_id=request_id, latency_ms=int((time.perf_counter()-start)*1000),
            retrieved_sources=[{'id': p['id'], 'url': p['source_url'], 'course_code': p.get('course_code'),
                                'similarity': p.get('similarity')} for p in result.get('passages', [])[:5]])
        logger.info(json.dumps({'request_id': request_id, 'status': response.status, 'latency_ms': response.latency_ms, 'sources': len(response.citations)}))
        return response
    except HTTPException:
        raise
    except Exception as exc:
        # Do not log exception strings, prompts, URLs with credentials, or transcripts.
        logger.error(json.dumps({'request_id': request_id, 'error_type': type(exc).__name__}))
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=ChatResponse(answer='The catalog service is temporarily unavailable. Please try again later.', status='error', request_id=request_id, latency_ms=int((time.perf_counter()-start)*1000)).model_dump())

"""Preserve full baseline; rerun only observed failures after corrective changes."""
import csv
import json
import time
from pathlib import Path
import httpx

cases=[json.loads(line) for line in Path('evals/questions.jsonl').read_text().splitlines()]
results=[]
with httpx.Client(timeout=60) as client:
    for case in cases:
        if case['id'] not in ['Q04','Q07','Q15']:
            continue
        start=time.perf_counter()
        r=client.post('https://uiuc-catalog-api-gyst-now.vercel.app/api/chat',json={'question':case['question']})
        data=r.json()
        results.append({'id':case['id'],'question':case['question'],'http_status':r.status_code,'latency_ms':round((time.perf_counter()-start)*1000),'response':data})
        print(json.dumps(results[-1]),flush=True)
        time.sleep(6.1)
Path('evals/retested-failures.json').write_text(json.dumps(results,indent=2)+'\n')

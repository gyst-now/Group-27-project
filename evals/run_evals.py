"""Run real API requests; leave semantic grades empty for human review."""
import argparse
import csv
import json
import math
import statistics
import time
from pathlib import Path
import httpx

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-url',default='http://localhost:8000')
    parser.add_argument('--output',default='evals/results.csv')
    args=parser.parse_args()
    cases=[json.loads(line) for line in Path('evals/questions.jsonl').read_text().splitlines()]
    rows=[]
    with httpx.Client(timeout=60) as client:
        for case in cases:
            start=time.perf_counter(); data={}; code=0
            try:
                response=client.post(args.base_url.rstrip('/')+'/api/chat',json={'question':case['question'],'catalog_year':'2026-27'})
                code=response.status_code
                data=response.json()
            except Exception as exc:
                data={'status':'error','answer':type(exc).__name__}
            sources={c['url'] for c in data.get('citations',[])}
            retrieved_urls={s['url'] for s in data.get('retrieved_sources',[])[:5]}
            rows.append({'id':case['id'],'question':case['question'],'category':case['category'],
                'http_status':code,'status':data.get('status','error'),'latency_ms':round((time.perf_counter()-start)*1000),
                'returned_source_coverage':int(set(case['expected_source_urls'])<=sources) if case['expected_source_urls'] else '',
                'retrieval_hit_at_5':int(set(case['expected_source_urls'])<=retrieved_urls) if case['expected_source_urls'] and data.get('retrieved_sources') else '',
                'retrieved_sources':json.dumps(data.get('retrieved_sources',[])),
                'faithfulness_human':'','citation_validity_human':'','no_answer_correct_human':'',
                'answer':data.get('answer',''),'citations':json.dumps(data.get('citations',[])),'request_id':data.get('request_id','')})
            print(case['id'],code,data.get('status','error'), flush=True)
            time.sleep(6.1) # Respect default per-IP public limit.
    with open(args.output,'w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    latencies=sorted(r['latency_ms'] for r in rows)
    summary={'requests':len(rows),'errors':sum(r['status']=='error' for r in rows),
        'all_request_p50_ms':statistics.median(latencies),'all_request_p95_ms':latencies[math.ceil(.95*len(latencies))-1],
        'answer_faithfulness':'not measured','citation_validity':'not measured','retrieval_hit_at_5':sum(r['retrieval_hit_at_5'] for r in rows if r['retrieval_hit_at_5'] != '') / sum(r['retrieval_hit_at_5'] != '' for r in rows) if any(r['retrieval_hit_at_5'] != '' for r in rows) else 'not measured',
        'note':'Retrieval hit@5 is source-URL coverage in the first five retrieved passages, not claim-level correctness. Semantic grades require explicit review.'}
    Path(args.output).with_suffix('.summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()

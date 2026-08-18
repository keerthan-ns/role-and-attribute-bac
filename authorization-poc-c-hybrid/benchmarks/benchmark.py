from __future__ import annotations
import argparse,json,statistics,time,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

def pct(xs,p):
    xs=sorted(xs)
    i=(len(xs)-1)*p/100
    lo=int(i)
    hi=min(lo+1,len(xs)-1)
    return xs[lo] if lo==hi else xs[lo]+(xs[hi]-xs[lo])*(i-lo)

def post(url,payload):
    req=urllib.request.Request(url,data=json.dumps(payload,separators=(',',':')).encode(),headers={'Content-Type':'application/json'},method='POST'); t=time.perf_counter_ns()
    try:
        with urllib.request.urlopen(req,timeout=10) as r: r.read()
        return (time.perf_counter_ns()-t)/1e6,True
    except Exception: 
        return (time.perf_counter_ns()-t)/1e6,False

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--scenario', choices=['openfga', 'opa', 'hybrid'], required=True)
    p.add_argument('--requests', type=int, default=10000)
    p.add_argument('--warmup', type=int, default=500)
    p.add_argument('--concurrency', type=int, default=32)
    p.add_argument('--openfga-url', default='http://localhost:8091')
    p.add_argument('--opa-url', default='http://localhost:8182')
    p.add_argument('--gateway-url', default='http://localhost:8090')
    p.add_argument('--store-id')
    p.add_argument('--model-id')
    p.add_argument('--user', default='user-0000000')
    p.add_argument('--resource', default='resource-00000000')
    p.add_argument('--output-dir', type=Path, default=Path('benchmarks/results'))
    a = p.parse_args()

    url = None
    payload = None

    if a.scenario == 'openfga':
        if not a.store_id or not a.model_id:
            raise SystemExit('--store-id and --model-id are required')
        url = f'{a.openfga_url}/stores/{a.store_id}/check'
        payload = {
            'authorization_model_id': a.model_id,
            'tuple_key': {
                'user': f'user:{a.user}',
                'relation': 'can_read',
                'object': f'resource:{a.resource}'
            }
        }
    elif a.scenario == 'opa':
        url = f'{a.opa_url}/v1/data/hybrid/authz/decision'
        payload = {
            'input': {
                'relationship_allowed': True,
                'action': 'read',
                'subject': {
                    'organization': 'org-0000',
                    'clearance': 5,
                    'role': 'developer',
                    'event_zone': 'ZONE-A'
                },
                'resource': {
                    'organization': 'org-0000',
                    'classification': 1,
                    'allowed_location': None,
                    'event_zone': 'ZONE-A'
                },
                'context': {
                    'location': 'BENGALURU',
                    'event_zone': 'ZONE-A'
                }
            }
        }
    elif a.scenario == 'hybrid':
        if not a.store_id or not a.model_id:
            raise SystemExit('--store-id and --model-id are required')
        url = f'{a.gateway_url}/authorize'
        payload = {
            'subject_id': a.user,
            'resource_id': a.resource,
            'action': 'read',
            'store_id': a.store_id,
            'model_id': a.model_id,
            'context': {
                'location': 'BENGALURU',
                'event_zone': 'ZONE-A'
            }
        }
    else:
        raise SystemExit(f'Unsupported scenario: {a.scenario}')

    if url is None or payload is None:
        raise SystemExit(f'Failed to initialize request for scenario: {a.scenario}')

    for _ in range(a.warmup):
        _, ok = post(url, payload)
        if not ok:
            raise SystemExit('warmup failed')

    t = time.perf_counter()
    samples = []
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        fs = [ex.submit(post, url, payload) for _ in range(a.requests)]
        for f in as_completed(fs):
            samples.append(f.result())

    wall = time.perf_counter() - t
    lat = [x[0] for x in samples]
    ok = sum(1 for x in samples if x[1])

    result = {
        'scenario': a.scenario,
        'requests': a.requests,
        'warmup': a.warmup,
        'concurrency': a.concurrency,
        'successful': ok,
        'errors': a.requests - ok,
        'wall_seconds': round(wall, 6),
        'requests_per_second': round(a.requests / wall, 3),
        'avg_ms': round(statistics.mean(lat), 4),
        'p50_ms': round(pct(lat, 50), 4),
        'p95_ms': round(pct(lat, 95), 4),
        'p99_ms': round(pct(lat, 99), 4),
        'p99_9_ms': round(pct(lat, 99.9), 4),
        'max_ms': round(max(lat), 4)
    }

    a.output_dir.mkdir(parents=True, exist_ok=True)
    out = a.output_dir / f'{a.scenario}-r{a.requests}-c{a.concurrency}.json'
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__=='__main__': 
   main()

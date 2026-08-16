from __future__ import annotations
import argparse,json,urllib.request
from pathlib import Path

def post(base,path,payload):
    req=urllib.request.Request(base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=60) as r: return json.loads(r.read()) if r.readable() else {}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base-url',default='http://localhost:8080')
    p.add_argument('--store-id',required=True)
    p.add_argument('--model-id',required=True)
    p.add_argument('--tuples',type=Path,default=Path('data/tuples.jsonl'))
    p.add_argument('--batch-size',type=int,default=100)
    args=p.parse_args()
    buf=[]; total=0
    with args.tuples.open(encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            buf.append(json.loads(line))
            if len(buf)==args.batch_size:
                post(args.base_url,f'/stores/{args.store_id}/write',{'authorization_model_id':args.model_id,'writes':{'tuple_keys':buf}})
                total+=len(buf); print(f'written={total}',flush=True); buf.clear()
    if buf:
        post(args.base_url,f'/stores/{args.store_id}/write',{'authorization_model_id':args.model_id,'writes':{'tuple_keys':buf}}); total+=len(buf)
    print('total_written=',total)
if __name__=='__main__': main()

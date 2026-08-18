from __future__ import annotations
import argparse,json,urllib.error,urllib.request
from pathlib import Path
def post(base,path,payload):
 req=urllib.request.Request(base.rstrip('/')+path,data=json.dumps(payload,separators=(',',':')).encode(),headers={'Content-Type':'application/json'},method='POST')
 try:
  with urllib.request.urlopen(req,timeout=60) as r: raw=r.read(); return json.loads(raw) if raw else {}
 except urllib.error.HTTPError as e: raise RuntimeError(f'OpenFGA write failed HTTP {e.code}: {e.read().decode(errors="replace")}')
def main():
 p=argparse.ArgumentParser(); p.add_argument('--base-url',default='http://localhost:8091'); p.add_argument('--store-id',required=True); p.add_argument('--model-id',required=True); p.add_argument('--tuples',type=Path,default=Path('data/tuples.jsonl')); p.add_argument('--batch-size',type=int,default=100); a=p.parse_args(); buf=[]; total=0
 with a.tuples.open(encoding='utf-8') as f:
  for line in f:
   if line.strip(): buf.append(json.loads(line))
   if len(buf)>=a.batch_size:
    post(a.base_url,f'/stores/{a.store_id}/write',{'authorization_model_id':a.model_id,'writes':{'tuple_keys':buf}}); total+=len(buf); print(f'written={total}',flush=True); buf.clear()
 if buf: post(a.base_url,f'/stores/{a.store_id}/write',{'authorization_model_id':a.model_id,'writes':{'tuple_keys':buf}}); total+=len(buf)
 print(f'total_written={total}')
if __name__=='__main__': main()

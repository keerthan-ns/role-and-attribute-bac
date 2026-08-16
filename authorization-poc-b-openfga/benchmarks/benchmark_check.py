#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,random,statistics,time,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
def pct(xs,p): return sorted(xs)[min(len(xs)-1,int((p/100)*(len(xs)-1)))]
def post(url,payload):
 b=json.dumps(payload).encode(); q=urllib.request.Request(url,data=b,headers={"Content-Type":"application/json"},method="POST"); t=time.perf_counter_ns()
 try:
  with urllib.request.urlopen(q,timeout=20) as r: r.read(); ok=True
 except Exception: ok=False
 return (time.perf_counter_ns()-t)/1e6,ok
def main():
 p=argparse.ArgumentParser(); p.add_argument("--api-url",default="http://localhost:8080"); p.add_argument("--store-id",required=True); p.add_argument("--model-id",required=True); p.add_argument("--attributes",default="data/attributes.json"); p.add_argument("--requests",type=int,default=10000); p.add_argument("--concurrency",type=int,default=32); p.add_argument("--seed",type=int,default=7); p.add_argument("--relation",default="can_read"); a=p.parse_args(); d=json.loads(Path(a.attributes).read_text()); users=list(d["users"]); resources=list(d["resources"]); r=random.Random(a.seed); qs=[]
 for _ in range(a.requests):
  u=r.choice(users); o=r.choice(resources); qs.append({"authorization_model_id":a.model_id,"tuple_key":{"user":f"user:{u}","relation":a.relation,"object":f"resource:{o}"}})
 url=f"{a.api_url}/stores/{a.store_id}/check"; start=time.perf_counter(); sam=[]; ok=0
 with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
  fs=[ex.submit(post,url,q) for q in qs]
  for f in as_completed(fs): ms,good=f.result(); sam.append(ms); ok+=int(good)
 wall=time.perf_counter()-start
 print(json.dumps({"requests":a.requests,"concurrency":a.concurrency,"successful":ok,"errors":a.requests-ok,"wall_seconds":round(wall,4),"throughput_req_s":round(a.requests/wall,2),"avg_ms":round(statistics.mean(sam),3),"p50_ms":round(pct(sam,50),3),"p95_ms":round(pct(sam,95),3),"p99_ms":round(pct(sam,99),3),"max_ms":round(max(sam),3)},indent=2))
if __name__=="__main__": main()

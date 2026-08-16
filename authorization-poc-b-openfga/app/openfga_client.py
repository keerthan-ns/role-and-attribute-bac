#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,sys,urllib.request,urllib.error
from pathlib import Path
BASE=os.getenv("FGA_API_URL","http://localhost:8080")
def req(method,path,payload=None,timeout=60):
 data=None if payload is None else json.dumps(payload).encode(); q=urllib.request.Request(BASE+path,data=data,headers={"Content-Type":"application/json"},method=method)
 try:
  with urllib.request.urlopen(q,timeout=timeout) as r: b=r.read(); return json.loads(b) if b else {}
 except urllib.error.HTTPError as e:
  print(e.read().decode(errors="replace"),file=sys.stderr); raise
def write_tuples(store,model,path,batch=100):
 buf=[]; total=0
 for line in Path(path).open(encoding="utf-8"):
  if not line.strip(): continue
  buf.append(json.loads(line))
  if len(buf)==batch:
   req("POST",f"/stores/{store}/write",{"writes":{"tuple_keys":buf},"authorization_model_id":model})
   total+=len(buf); print(f"written={total}",flush=True); buf=[]
 if buf: req("POST",f"/stores/{store}/write",{"writes":{"tuple_keys":buf},"authorization_model_id":model}); total+=len(buf)
 print(f"total_written={total}")
def check(store,model,user,relation,obj):
 return req("POST",f"/stores/{store}/check",{"authorization_model_id":model,"tuple_key":{"user":user,"relation":relation,"object":obj}})
def list_objects(store,model,user,relation,typ):
 return req("POST",f"/stores/{store}/list-objects",{"authorization_model_id":model,"user":user,"relation":relation,"type":typ})
def batch_check(store,model,checks):
 return req("POST",f"/stores/{store}/batch-check",{"authorization_model_id":model,"checks":[{"correlation_id":str(i),"tuple_key":c} for i,c in enumerate(checks)]})
def main():
 p=argparse.ArgumentParser(); s=p.add_subparsers(dest="cmd",required=True)
 x=s.add_parser("write-tuples"); x.add_argument("--store-id",required=True); x.add_argument("--model-id",required=True); x.add_argument("--tuples",default="data/tuples.jsonl"); x.add_argument("--batch-size",type=int,default=100)
 x=s.add_parser("check"); x.add_argument("--store-id",required=True); x.add_argument("--model-id",required=True); x.add_argument("--user",required=True); x.add_argument("--relation",required=True); x.add_argument("--object",required=True)
 x=s.add_parser("list-objects"); x.add_argument("--store-id",required=True); x.add_argument("--model-id",required=True); x.add_argument("--user",required=True); x.add_argument("--relation",required=True); x.add_argument("--type",default="resource")
 if False: pass
 a=p.parse_args()
 if a.cmd=="write-tuples": write_tuples(a.store_id,a.model_id,a.tuples,a.batch_size)
 elif a.cmd=="check": print(json.dumps(check(a.store_id,a.model_id,a.user,a.relation,a.object),indent=2))
 elif a.cmd=="list-objects": print(json.dumps(list_objects(a.store_id,a.model_id,a.user,a.relation,a.type),indent=2))
if __name__=="__main__": main()

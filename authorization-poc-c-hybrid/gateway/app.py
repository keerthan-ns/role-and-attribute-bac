from __future__ import annotations
import json, os, time, urllib.error, urllib.request
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
FGA_URL=os.getenv("FGA_URL","http://openfga:8080"); OPA_URL=os.getenv("OPA_URL","http://opa:8181"); DEFAULT_STORE=os.getenv("FGA_STORE_ID",""); DEFAULT_MODEL=os.getenv("FGA_MODEL_ID","")
DATA=json.loads(Path(os.getenv("ATTRIBUTES_FILE","/data/attributes.json")).read_text(encoding="utf-8"))
app=FastAPI(title="POC-C Hybrid Authorization Gateway")
class AuthorizationRequest(BaseModel):
    subject_id:str; resource_id:str; action:str; context:dict[str,Any]=Field(default_factory=dict); store_id:str|None=None; model_id:str|None=None
def post_json(url,payload,timeout=5):
    req=urllib.request.Request(url,data=json.dumps(payload,separators=(",",":")).encode(),headers={"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e: raise HTTPException(502,detail={"status":e.code,"body":e.read().decode(errors="replace")})
    except Exception as e: raise HTTPException(502,detail=str(e))
def attrs(s,r):
    try:return DATA["users"][s],DATA["resources"][r]
    except KeyError: raise HTTPException(400,detail="Unknown subject_id/resource_id")
@app.get("/health")
def health(): return {"status":"ok","attributes_loaded":bool(DATA.get("users")) and bool(DATA.get("resources"))}
@app.post("/authorize")
def authorize(x:AuthorizationRequest):
    store=x.store_id or DEFAULT_STORE; model=x.model_id or DEFAULT_MODEL
    if not store or not model: raise HTTPException(500,detail="store_id/model_id required")
    subject,resource=attrs(x.subject_id,x.resource_id); relation="can_read" if x.action=="read" else "can_write"
    t0=time.perf_counter_ns(); fga=post_json(f"{FGA_URL}/stores/{store}/check",{"authorization_model_id":model,"tuple_key":{"user":f"user:{x.subject_id}","relation":relation,"object":f"resource:{x.resource_id}"}}); fga_ms=(time.perf_counter_ns()-t0)/1e6
    rel=bool(fga.get("allowed")); t1=time.perf_counter_ns(); opa=post_json(f"{OPA_URL}/v1/data/hybrid/authz/decision",{"input":{"subject":subject,"resource":resource,"action":x.action,"context":x.context,"relationship_allowed":rel}}); opa_ms=(time.perf_counter_ns()-t1)/1e6
    return {"decision":opa.get("result"),"relationship_check":fga,"policy_decision":opa.get("result"),"timings_ms":{"openfga":round(fga_ms,4),"opa":round(opa_ms,4),"gateway_total":round(fga_ms+opa_ms,4)}}

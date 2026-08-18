#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,random
from pathlib import Path
ROLES=["viewer","developer","operator","security_officer","admin"]
LOCS=["DELHI","BENGALURU","MUMBAI","HYDERABAD","CHENNAI"]
ZONES=["ZONE-A","ZONE-B","ZONE-C","ZONE-D"]
def main():
 p=argparse.ArgumentParser(); p.add_argument("--seed",type=int,default=42); p.add_argument("--users",type=int,default=50000); p.add_argument("--resources",type=int,default=20000); p.add_argument("--orgs",type=int,default=100); p.add_argument("--departments",type=int,default=1000); p.add_argument("--teams",type=int,default=5000); p.add_argument("--applications",type=int,default=500); p.add_argument("--output",type=Path,default=Path("data/tuples.jsonl")); p.add_argument("--attributes-output",type=Path,default=Path("data/attributes.json")); a=p.parse_args(); r=random.Random(a.seed)
 orgs=[f"org-{i:04d}" for i in range(a.orgs)]; depts={f"dept-{i:05d}":r.choice(orgs) for i in range(a.departments)}; teams={f"team-{i:05d}":r.choice(list(depts)) for i in range(a.teams)}; tbd={d:[] for d in depts}
 for t,d in teams.items(): tbd[d].append(t)
 apps=[f"app-{i:05d}" for i in range(a.applications)]; users={}; lines=[]
 for i in range(a.users):
  uid=f"user-{i:07d}"; d=r.choice(list(depts)); t=r.choice(tbd[d]) if tbd[d] else None; role=r.choice(ROLES); u={"department":d,"team":t,"organization":depts[d],"role":role,"clearance":r.randint(1,5),"location":r.choice(LOCS),"event_zone":r.choice(ZONES)}; users[uid]=u
  lines += [{"user":f"user:{uid}","relation":"member","object":f"department:{d}"},{"user":f"user:{uid}","relation":"member","object":f"organization:{depts[d]}"},{"user":f"user:{uid}","relation":"member","object":f"role:{role}"}]
  if t: lines.append({"user":f"user:{uid}","relation":"member","object":f"team:{t}"})
 for d,o in depts.items(): lines.append({"user":f"organization:{o}","relation":"organization","object":f"department:{d}"})
 for t,d in teams.items(): lines.append({"user":f"department:{d}","relation":"department","object":f"team:{t}"})
 res={}
 for i in range(a.resources):
  rid=f"resource-{i:08d}"; d=r.choice(list(depts)); o=depts[d]; t=r.choice(tbd[d]) if tbd[d] else None; app=r.choice(apps); m={"department":d,"organization":o,"team":t,"application":app,"type":r.choice(["application","service","feature","document","facility"]),"classification":r.randint(1,5),"allowed_location":r.choice([None]+LOCS),"event_zone":r.choice(ZONES)}; res[rid]=m
  lines += [{"user":f"organization:{o}","relation":"organization","object":f"resource:{rid}"},{"user":f"department:{d}","relation":"department","object":f"resource:{rid}"},{"user":f"application:{app}","relation":"application","object":f"resource:{rid}"},{"user":"role:viewer#member","relation":"viewer","object":f"resource:{rid}"},{"user":"role:developer#member","relation":"editor","object":f"resource:{rid}"},{"user":"role:admin#member","relation":"admin","object":f"resource:{rid}"}]
  if t: lines.append({"user":f"team:{t}","relation":"team","object":f"resource:{rid}"})
  if m["classification"]>=4: lines.append({"user":"role:security_officer#member","relation":"viewer","object":f"resource:{rid}"})
  if m["classification"]<=3: lines.append({"user":"role:operator#member","relation":"editor","object":f"resource:{rid}"})
 a.output.parent.mkdir(parents=True,exist_ok=True); a.attributes_output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open("w",encoding="utf-8") as f:
  for x in lines: f.write(json.dumps(x,separators=(",",":"))+"\n")
 a.attributes_output.write_text(json.dumps({"users":users,"resources":res,"seed":a.seed},separators=(",",":")),encoding="utf-8"); print(f"tuples={len(lines):,}")
if __name__=="__main__": main()

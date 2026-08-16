import json
from pathlib import Path
p=Path('data/tuples.jsonl')
counts={}
invalid=[]
for line in p.open(encoding='utf-8'):
    t=json.loads(line)
    key=(t['user'],t['relation'],t['object'].split(':')[0])
    counts[key]=counts.get(key,0)+1
    if t['user'].startswith('role:') and t['relation'] in {'viewer','editor','admin'} and not t['user'].endswith('#member'):
        invalid.append(t)
print('tuple_count=',sum(counts.values()))
print('invalid_role_permission_tuples=',len(invalid))
if invalid:
    print('first_invalid=',invalid[:3])
    raise SystemExit(1)

#!/usr/bin/env python3
"""Generate deterministic authorization data for POC-A.

Example:
  python scripts/generate_dataset.py --users 1000000 --resources 5000000 --output opa/data/large-data.json
"""
from __future__ import annotations

import argparse, json, random
from pathlib import Path

LOCATIONS = ["DELHI", "BENGALURU", "MUMBAI", "HYDERABAD", "CHENNAI"]
ZONES = ["ZONE-A", "ZONE-B", "ZONE-C", "ZONE-D"]
ROLES = ["viewer", "developer", "operator", "security_officer", "admin"]

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--users", type=int, default=50_000)
    p.add_argument("--resources", type=int, default=20_000)
    p.add_argument("--orgs", type=int, default=100)
    p.add_argument("--departments", type=int, default=1_000)
    p.add_argument("--teams", type=int, default=5_000)
    p.add_argument("--output", type=Path, default=Path("opa/data/generated-data.json"))
    args = p.parse_args()
    rng = random.Random(args.seed)

    orgs = [f"org-{i:04d}" for i in range(args.orgs)]
    depts = {f"dept-{i:05d}": rng.choice(orgs) for i in range(args.departments)}
    teams = {f"team-{i:05d}": rng.choice(list(depts)) for i in range(args.teams)}

    # Build an index to avoid scanning every team when generating users.
    teams_by_dept: dict[str, list[str]] = {d: [] for d in depts}
    for team, dept in teams.items():
        teams_by_dept[dept].append(team)

    users = {}
    for i in range(args.users):
        uid = f"user-{i:07d}"
        dept = rng.choice(list(depts))
        team = rng.choice(teams_by_dept[dept]) if teams_by_dept[dept] else None
        users[uid] = {
            "org_id": depts[dept],
            "department_id": dept,
            "team_id": team,
            "roles": rng.sample(ROLES, k=1 if rng.random() < 0.8 else 2),
            "clearance": rng.randint(1, 5),
            "location": rng.choice(LOCATIONS),
            "event_zone": rng.choice(ZONES),
            "employment_type": rng.choice(["EMPLOYEE", "CONTRACTOR", "VENDOR"]),
        }

    resources = {}
    for i in range(args.resources):
        rid = f"resource-{i:08d}"
        dept = rng.choice(list(depts))
        resources[rid] = {
            "type": rng.choice(["application", "service", "feature", "document", "facility"]),
            "org_id": depts[dept],
            "department_id": dept,
            "classification": rng.randint(1, 5),
            "allowed_location": rng.choice([None] + LOCATIONS),
            "event_zone": rng.choice(ZONES),
        }

    payload = {
        "meta": vars(args) | {"schema_version": 1},
        "orgs": orgs,
        "departments": depts,
        "teams": teams,
        "users": users,
        "resources": resources,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))

    print(f"Wrote {args.output}")
    print(json.dumps(payload["meta"], indent=2, default=str))

if __name__ == "__main__":
    main()

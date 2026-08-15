#!/usr/bin/env python3
"""Simple OPA HTTP benchmark for POC-A."""
from __future__ import annotations
import argparse, json, random, statistics, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import urllib.request

def post(url: str, payload: dict, timeout: float) -> tuple[float, bool]:
    body = json.dumps({"input": payload}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    start = time.perf_counter_ns()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            _ = r.read()
        ok = True
    except Exception:
        ok = False
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
    return elapsed_ms, ok

def build_requests(data: dict, n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    users = list(data["users"].items())
    resources = list(data["resources"].items())
    reqs = []
    for _ in range(n):
        uid, user = rng.choice(users)
        rid, resource = rng.choice(resources)
        reqs.append({
            "subject": {"id": uid, **user},
            "resource": {"id": rid, **resource},
            "action": rng.choice(["read", "write", "admin"]),
            "context": {
                "location": rng.choice(["DELHI", "BENGALURU", "MUMBAI", "HYDERABAD", "CHENNAI"]),
                "event_id": "national-event-2026",
            },
        })
    return reqs

def percentile(xs: list[float], p: float) -> float:
    if not xs:
        return float("nan")
    xs = sorted(xs)
    idx = min(len(xs)-1, max(0, int(round((p/100)*(len(xs)-1)))))
    return xs[idx]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--opa-url", default="http://localhost:8181/v1/data/authz/decision")
    ap.add_argument("--data", type=Path, default=Path("opa/data/dev-data.json"))
    ap.add_argument("--requests", type=int, default=10_000)
    ap.add_argument("--concurrency", type=int, default=32)
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    data = json.loads(args.data.read_text(encoding="utf-8"))
    reqs = build_requests(data, args.requests, args.seed)

    started = time.perf_counter()
    samples = []
    ok_count = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(post, args.opa_url, r, args.timeout) for r in reqs]
        for f in as_completed(futures):
            ms, ok = f.result()
            samples.append(ms)
            ok_count += int(ok)
    wall = time.perf_counter() - started

    print(json.dumps({
        "requests": args.requests,
        "concurrency": args.concurrency,
        "successful": ok_count,
        "errors": args.requests - ok_count,
        "wall_seconds": round(wall, 4),
        "throughput_req_s": round(args.requests / wall, 2),
        "p50_ms": round(percentile(samples, 50), 3),
        "p95_ms": round(percentile(samples, 95), 3),
        "p99_ms": round(percentile(samples, 99), 3),
        "min_ms": round(min(samples), 3),
        "max_ms": round(max(samples), 3),
        "avg_ms": round(statistics.mean(samples), 3),
    }, indent=2))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Summarize JSON benchmark result files into a CSV-like table.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


FIELDS = [
    "scenario",
    "requests",
    "http_requests",
    "concurrency",
    "batch_size",
    "successful_http_requests",
    "errors",
    "wall_seconds",
    "http_requests_per_second",
    "logical_checks_per_second",
    "avg_ms",
    "p50_ms",
    "p95_ms",
    "p99_ms",
    "p99_9_ms",
    "max_ms",
    "allowed_true",
    "allowed_false",
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", type=Path, default=Path("benchmarks/results"))
    p.add_argument("--output", type=Path, default=Path("benchmarks/results/summary.csv"))
    args = p.parse_args()

    rows = []
    for file in sorted(args.input_dir.glob("*.json")):
        if file.name == args.output.name:
            continue
        rows.append(json.loads(file.read_text(encoding="utf-8")))

    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in FIELDS})

    print(f"Wrote {len(rows)} rows -> {args.output}")


if __name__ == "__main__":
    main()

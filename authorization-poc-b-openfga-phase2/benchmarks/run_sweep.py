#!/usr/bin/env python3
"""
Run a standard Phase-2 benchmark matrix.

Examples:
  python benchmarks/run_sweep.py
  python benchmarks/run_sweep.py --scenarios check condition contextual batch-check list-objects
  python benchmarks/run_sweep.py --concurrency 1 4 8 16 32 64 128 256
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_CONCURRENCY = [1, 4, 8, 16, 32, 64, 128, 256]
DEFAULT_SCENARIOS = [
    "check",
    "condition",
    "contextual",
    "batch-check",
    "list-objects",
    "consistency-min",
    "consistency-high",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", nargs="+", default=DEFAULT_SCENARIOS)
    parser.add_argument("--concurrency", nargs="+", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--requests", type=int, default=10000)
    parser.add_argument("--warmup", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--user", default="user-0000000")
    parser.add_argument("--resource", default="resource-00000000")
    parser.add_argument("--attributes", default="data/attributes.json")
    parser.add_argument("--store-id", required=False)
    parser.add_argument("--baseline-model-id", required=False)
    parser.add_argument("--condition-model-id", required=False)
    parser.add_argument("--contextual-model-id", required=False)

    args = parser.parse_args()

    for scenario in args.scenarios:
        for concurrency in args.concurrency:
            cmd = [
                sys.executable,
                "benchmarks/benchmark.py",
                "--scenario", scenario,
                "--requests", str(args.requests),
                "--warmup", str(args.warmup),
                "--concurrency", str(concurrency),
                "--batch-size", str(args.batch_size),
                "--user", args.user,
                "--resource", args.resource,
                "--attributes", args.attributes,
            ]

            if args.store_id:
                cmd += ["--store-id", args.store_id]
            if args.baseline_model_id:
                cmd += ["--baseline-model-id", args.baseline_model_id]
            if args.condition_model_id:
                cmd += ["--condition-model-id", args.condition_model_id]
            if args.contextual_model_id:
                cmd += ["--contextual-model-id", args.contextual_model_id]

            print("\n" + "=" * 88)
            print("Running:", " ".join(cmd))
            print("=" * 88)

            completed = subprocess.run(cmd)
            if completed.returncode != 0:
                raise SystemExit(
                    f"Benchmark failed: scenario={scenario}, concurrency={concurrency}, "
                    f"exit_code={completed.returncode}"
                )


if __name__ == "__main__":
    main()

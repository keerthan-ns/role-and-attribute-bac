#!/usr/bin/env python3
"""
Reusable OpenFGA Phase-2 benchmark harness.

Scenarios:
  check
  condition
  contextual
  batch-check
  list-objects
  consistency-min
  consistency-high

Examples:
  python benchmarks/benchmark.py --scenario check --requests 10000 --concurrency 32
  python benchmarks/benchmark.py --scenario batch-check --requests 10000 --batch-size 50 --concurrency 32

Environment variables:
  BASE_URL            default http://localhost:8080
  STORE_ID            required
  BASELINE_MODEL_ID   required for check/list/consistency
  CONDITION_MODEL_ID  required for condition
  CONTEXTUAL_MODEL_ID required for contextual/batch-check
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
DEFAULT_ATTRIBUTES = Path("data/attributes.json")


@dataclass
class Sample:
    latency_ms: float
    ok: bool
    allowed: bool | None
    error: str | None = None


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    values = sorted(values)
    rank = (len(values) - 1) * (p / 100.0)
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return values[lo]
    return values[lo] + (values[hi] - values[lo]) * (rank - lo)


def http_post(base_url: str, path: str, payload: dict[str, Any], timeout: float) -> tuple[float, bool, dict[str, Any] | None, str | None]:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter_ns()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
        latency = (time.perf_counter_ns() - started) / 1_000_000
        result = json.loads(raw) if raw else {}
        return latency, True, result, None
    except Exception as exc:
        latency = (time.perf_counter_ns() - started) / 1_000_000
        return latency, False, None, str(exc)


def load_users_and_resources(path: Path) -> tuple[list[str], list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data["users"].keys()), list(data["resources"].keys())


def build_check_payload(model_id: str, user_id: str, resource_id: str, relation: str) -> dict[str, Any]:
    return {
        "authorization_model_id": model_id,
        "tuple_key": {
            "user": f"user:{user_id}",
            "relation": relation,
            "object": f"resource:{resource_id}",
        },
    }


def build_condition_payload(model_id: str, user_id: str, resource_id: str, current_time: str) -> dict[str, Any]:
    return {
        "authorization_model_id": model_id,
        "tuple_key": {
            "user": f"user:{user_id}",
            "relation": "temporary_viewer",
            "object": f"resource:{resource_id}",
        },
        "context": {
            "current_time": current_time,
        },
    }


def build_contextual_payload(model_id: str, user_id: str, resource_id: str) -> dict[str, Any]:
    tuple_value = {
        "user": f"user:{user_id}",
        "relation": "emergency_viewer",
        "object": f"resource:{resource_id}",
    }
    return {
        "authorization_model_id": model_id,
        "tuple_key": tuple_value,
        "contextual_tuples": {
            "tuple_keys": [tuple_value],
        },
    }


def build_list_objects_payload(model_id: str, user_id: str, relation: str, object_type: str) -> dict[str, Any]:
    return {
        "authorization_model_id": model_id,
        "type": object_type,
        "relation": relation,
        "user": f"user:{user_id}",
    }


def build_batch_payload(model_id: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "authorization_model_id": model_id,
        "checks": checks,
    }


def warmup(
    base_url: str,
    path: str,
    payload_factory,
    warmup_requests: int,
    timeout: float,
) -> None:
    for i in range(warmup_requests):
        payload = payload_factory(i)
        _, ok, _, error = http_post(base_url, path, payload, timeout)
        if not ok:
            raise RuntimeError(f"Warm-up request failed: {error}")


def run_requests(
    base_url: str,
    path: str,
    payloads: list[dict[str, Any]],
    concurrency: int,
    timeout: float,
) -> list[Sample]:
    samples: list[Sample] = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(http_post, base_url, path, payload, timeout)
            for payload in payloads
        ]

        for future in as_completed(futures):
            latency, ok, result, error = future.result()
            allowed = None
            if isinstance(result, dict) and "allowed" in result:
                allowed = bool(result["allowed"])
            samples.append(Sample(latency, ok, allowed, error))

    return samples


def summarize(
    scenario: str,
    concurrency: int,
    logical_checks: int,
    http_requests: int,
    samples: list[Sample],
    wall_seconds: float,
    batch_size: int | None,
    args: argparse.Namespace,
) -> dict[str, Any]:
    latencies = [s.latency_ms for s in samples]
    success = sum(1 for s in samples if s.ok)
    errors = len(samples) - success

    result = {
        "scenario": scenario,
        "requests": logical_checks,
        "http_requests": http_requests,
        "concurrency": concurrency,
        "batch_size": batch_size,
        "successful_http_requests": success,
        "errors": errors,
        "wall_seconds": round(wall_seconds, 6),
        "http_requests_per_second": round(http_requests / wall_seconds, 3) if wall_seconds else None,
        "logical_checks_per_second": round(logical_checks / wall_seconds, 3) if wall_seconds else None,
        "avg_ms": round(statistics.mean(latencies), 4) if latencies else None,
        "p50_ms": round(percentile(latencies, 50), 4) if latencies else None,
        "p95_ms": round(percentile(latencies, 95), 4) if latencies else None,
        "p99_ms": round(percentile(latencies, 99), 4) if latencies else None,
        "p99_9_ms": round(percentile(latencies, 99.9), 4) if latencies else None,
        "max_ms": round(max(latencies), 4) if latencies else None,
        "allowed_true": sum(1 for s in samples if s.allowed is True),
        "allowed_false": sum(1 for s in samples if s.allowed is False),
        "base_url": args.base_url,
        "store_id": args.store_id,
        # "model_id": args.model_id,
        "model_id": getattr(args, "model_id", None)
    }

    if scenario == "batch-check":
        result["batch_size"] = batch_size

    return result


def resolve_required(name: str, value: str | None) -> str:
    if value:
        return value
    raise SystemExit(f"Missing required value: --{name.replace('_', '-')} or corresponding environment variable.")


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenFGA Phase-2 benchmark harness")
    parser.add_argument(
        "--scenario",
        required=True,
        choices=[
            "check",
            "condition",
            "contextual",
            "batch-check",
            "list-objects",
            "consistency-min",
            "consistency-high",
        ],
    )
    parser.add_argument("--requests", type=int, default=10_000)
    parser.add_argument("--concurrency", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=500)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--store-id", default=os.getenv("STORE_ID"))
    parser.add_argument("--baseline-model-id", default=os.getenv("BASELINE_MODEL_ID"))
    parser.add_argument("--condition-model-id", default=os.getenv("CONDITION_MODEL_ID"))
    parser.add_argument("--contextual-model-id", default=os.getenv("CONTEXTUAL_MODEL_ID"))
    parser.add_argument("--attributes", type=Path, default=DEFAULT_ATTRIBUTES)
    parser.add_argument("--user", default="user-0000000")
    parser.add_argument("--resource", default="resource-00000000")
    parser.add_argument("--relation", default="can_read")
    parser.add_argument("--output-dir", type=Path, default=Path("benchmarks/results"))
    parser.add_argument("--condition-current-time", default="2026-08-16T12:30:00Z")
    args = parser.parse_args()

    args.store_id = resolve_required("store_id", args.store_id)

    rng = random.Random(args.seed)
    users, resources = load_users_and_resources(args.attributes)

    scenario = args.scenario

    if scenario in {"check", "consistency-min", "consistency-high"}:
        model_id = resolve_required("baseline_model_id", args.baseline_model_id)
        args.model_id = model_id
        path = f"/stores/{args.store_id}/check"
        consistency = {
            "consistency-min": "MINIMIZE_LATENCY",
            "consistency-high": "HIGHER_CONSISTENCY",
        }.get(scenario)

        def make_payload(i: int) -> dict[str, Any]:
            # Deterministic request mix. Supplying --user/--resource pins the
            # benchmark to a repeatable hot pair; otherwise use the seeded mix.
            user = args.user if args.user else rng.choice(users)
            resource = args.resource if args.resource else rng.choice(resources)
            payload = build_check_payload(model_id, user, resource, args.relation)
            if consistency:
                payload["consistency"] = consistency
            return payload

        payloads = [
            make_payload(i)
            for i in range(args.requests)
        ]
        warmup(args.base_url, path, make_payload, args.warmup, args.timeout)

    elif scenario == "condition":
        model_id = resolve_required("condition_model_id", args.condition_model_id)
        args.model_id = model_id
        path = f"/stores/{args.store_id}/check"

        def make_payload(_i: int) -> dict[str, Any]:
            return build_condition_payload(
                model_id,
                args.user,
                args.resource,
                args.condition_current_time,
            )

        payloads = [make_payload(i) for i in range(args.requests)]
        warmup(args.base_url, path, make_payload, args.warmup, args.timeout)

    elif scenario == "contextual":
        model_id = resolve_required("contextual_model_id", args.contextual_model_id)
        args.model_id = model_id
        path = f"/stores/{args.store_id}/check"

        def make_payload(_i: int) -> dict[str, Any]:
            return build_contextual_payload(model_id, args.user, args.resource)

        payloads = [make_payload(i) for i in range(args.requests)]
        warmup(args.base_url, path, make_payload, args.warmup, args.timeout)

    elif scenario == "batch-check":
        model_id = resolve_required("contextual_model_id", args.contextual_model_id)
        path = f"/stores/{args.store_id}/batch-check"

        if args.batch_size <= 0:
            raise SystemExit("--batch-size must be > 0")

        batches = math.ceil(args.requests / args.batch_size)
        logical_counts: list[int] = []

        payloads = []
        remaining = args.requests
        for batch_index in range(batches):
            count = min(args.batch_size, remaining)
            remaining -= count
            checks = []

            for item_index in range(count):
                user = users[(batch_index * args.batch_size + item_index) % len(users)]
                resource = args.resource
                tuple_value = {
                    "user": f"user:{user}",
                    "relation": "emergency_viewer",
                    "object": f"resource:{resource}",
                }
                checks.append({
                    "correlation_id": f"b{batch_index}-c{item_index}",
                    "tuple_key": tuple_value,
                    "contextual_tuples": {
                        "tuple_keys": [tuple_value],
                    },
                })

            payloads.append(build_batch_payload(model_id, checks))
            logical_counts.append(count)

        # Warmup uses the first batch as representative.
        warmup_payload = payloads[0]

        def make_payload(_i: int) -> dict[str, Any]:
            return warmup_payload

        warmup(args.base_url, path, make_payload, min(args.warmup, len(payloads)), args.timeout)

    elif scenario == "list-objects":
        model_id = resolve_required("baseline_model_id", args.baseline_model_id)
        args.model_id = model_id
        path = f"/stores/{args.store_id}/list-objects"

        def make_payload(_i: int) -> dict[str, Any]:
            return build_list_objects_payload(model_id, args.user, args.relation, "resource")

        payloads = [make_payload(i) for i in range(args.requests)]
        warmup(args.base_url, path, make_payload, min(args.warmup, 100), args.timeout)

    else:
        raise AssertionError("unreachable")

    started = time.perf_counter()
    samples = run_requests(
        args.base_url,
        path,
        payloads,
        args.concurrency,
        args.timeout,
    )
    wall = time.perf_counter() - started

    logical_checks = args.requests
    http_requests = len(payloads)

    result = summarize(
        scenario=scenario,
        concurrency=args.concurrency,
        logical_checks=logical_checks,
        http_requests=http_requests,
        samples=samples,
        wall_seconds=wall,
        batch_size=args.batch_size if scenario == "batch-check" else None,
        args=args,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"{scenario}-"
        f"r{args.requests}-"
        f"c{args.concurrency}"
        + (f"-b{args.batch_size}" if scenario == "batch-check" else "")
        + ".json"
    )
    output_path = args.output_dir / filename
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()

"""
Performance thresholds and headless load test runner.

Usage:
    python -m loadtests.runner --users 50 --spawn-rate 5 --duration 60

Exits with code 1 if any threshold is breached.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

THRESHOLDS = {
    "p95_response_time_ms": 800,
    "p99_response_time_ms": 2000,
    "max_response_time_ms": 5000,
    "failure_rate_percent": 1.0,
    "min_requests_per_second": 10,
}


def run_locust(host, users, spawn_rate, duration):
    stats_file = Path(tempfile.mkdtemp()) / "locust_stats"

    cmd = [
        sys.executable, "-m", "locust",
        "-f", str(Path(__file__).parent / "locustfile.py"),
        "--host", host,
        "--headless",
        "-u", str(users),
        "-r", str(spawn_rate),
        "-t", f"{duration}s",
        "--csv", str(stats_file),
        "--csv-full-history",
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return stats_file, result.returncode


def parse_stats(stats_file):
    stats_path = Path(f"{stats_file}_stats.csv")
    if not stats_path.exists():
        print(f"ERROR: Stats file not found: {stats_path}")
        return None

    import csv
    with open(stats_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    aggregated = None
    for row in rows:
        if row.get("Name") == "Aggregated":
            aggregated = row
            break

    if not aggregated:
        print("ERROR: No aggregated stats found")
        return None

    total_requests = int(aggregated.get("Request Count", 0))
    total_failures = int(aggregated.get("Failure Count", 0))
    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

    return {
        "total_requests": total_requests,
        "total_failures": total_failures,
        "failure_rate_percent": failure_rate,
        "avg_response_time_ms": float(aggregated.get("Average Response Time", 0)),
        "p50_response_time_ms": float(aggregated.get("50%", 0)),
        "p95_response_time_ms": float(aggregated.get("95%", 0)),
        "p99_response_time_ms": float(aggregated.get("99%", 0)),
        "max_response_time_ms": float(aggregated.get("Max Response Time", 0)),
        "requests_per_second": float(aggregated.get("Requests/s", 0)),
    }


def check_thresholds(stats):
    violations = []

    if stats["p95_response_time_ms"] > THRESHOLDS["p95_response_time_ms"]:
        violations.append(
            f"p95 response time {stats['p95_response_time_ms']:.0f}ms "
            f"> {THRESHOLDS['p95_response_time_ms']}ms threshold"
        )

    if stats["p99_response_time_ms"] > THRESHOLDS["p99_response_time_ms"]:
        violations.append(
            f"p99 response time {stats['p99_response_time_ms']:.0f}ms "
            f"> {THRESHOLDS['p99_response_time_ms']}ms threshold"
        )

    if stats["max_response_time_ms"] > THRESHOLDS["max_response_time_ms"]:
        violations.append(
            f"Max response time {stats['max_response_time_ms']:.0f}ms "
            f"> {THRESHOLDS['max_response_time_ms']}ms threshold"
        )

    if stats["failure_rate_percent"] > THRESHOLDS["failure_rate_percent"]:
        violations.append(
            f"Failure rate {stats['failure_rate_percent']:.2f}% "
            f"> {THRESHOLDS['failure_rate_percent']}% threshold"
        )

    if stats["requests_per_second"] < THRESHOLDS["min_requests_per_second"]:
        violations.append(
            f"Throughput {stats['requests_per_second']:.1f} req/s "
            f"< {THRESHOLDS['min_requests_per_second']} req/s threshold"
        )

    return violations


def main():
    parser = argparse.ArgumentParser(description="Load test runner with threshold checks")
    parser.add_argument("--host", default="http://localhost:8000", help="Target host")
    parser.add_argument("--users", type=int, default=50, help="Peak concurrent users")
    parser.add_argument("--spawn-rate", type=int, default=5, help="Users spawned per second")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--thresholds-only", action="store_true",
                        help="Only parse existing stats without running Locust")
    parser.add_argument("--stats-file", help="Path to existing stats file prefix")
    args = parser.parse_args()

    if args.thresholds_only and args.stats_file:
        stats_file = args.stats_file
    else:
        stats_file, exit_code = run_locust(args.host, args.users, args.spawn_rate, args.duration)
        if exit_code != 0:
            print(f"Locust exited with code {exit_code}")
            sys.exit(exit_code)

    stats = parse_stats(stats_file)
    if stats is None:
        sys.exit(1)

    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS")
    print("=" * 60)
    print(f"  Total requests:     {stats['total_requests']}")
    print(f"  Total failures:     {stats['total_failures']}")
    print(f"  Failure rate:       {stats['failure_rate_percent']:.2f}%")
    print(f"  Avg response time:  {stats['avg_response_time_ms']:.0f}ms")
    print(f"  p50 response time:  {stats['p50_response_time_ms']:.0f}ms")
    print(f"  p95 response time:  {stats['p95_response_time_ms']:.0f}ms")
    print(f"  p99 response time:  {stats['p99_response_time_ms']:.0f}ms")
    print(f"  Max response time:  {stats['max_response_time_ms']:.0f}ms")
    print(f"  Throughput:         {stats['requests_per_second']:.1f} req/s")
    print("=" * 60)

    violations = check_thresholds(stats)
    if violations:
        print("\nTHRESHOLD VIOLATIONS:")
        for v in violations:
            print(f"  FAIL: {v}")
        print(f"\n{len(violations)} threshold(s) breached.")
        sys.exit(1)
    else:
        print("\nAll thresholds passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()

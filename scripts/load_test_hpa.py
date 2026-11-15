#!/usr/bin/env python3
"""
Lightweight sustained concurrent HTTP load test for Kubernetes HPA demonstration.
Uses Python standard library only (no pip dependencies required).
Supports Ctrl+C graceful termination and real-time throughput reporting.
"""

import os
import sys
import time
import signal
import argparse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

stop_requested = False

def sig_handler(sig, frame):
    global stop_requested
    stop_requested = True

signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)

def run_load_test(target_url: str, endpoint: str, concurrency: int):
    global stop_requested
    
    full_url = f"{target_url.rstrip('/')}/{endpoint.lstrip('/')}"
    print("=" * 70)
    print("🚀 SUSTAINED CONCURRENT HPA LOAD GENERATOR")
    print("=" * 70)
    print(f"Target URL   : {full_url}")
    print(f"Concurrency  : {concurrency} parallel worker threads")
    print("Press Ctrl+C at any time to stop load and observe HPA scale-down.")
    print("=" * 70)

    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    start_time = time.time()
    last_report_time = start_time

    def fetch():
        nonlocal total_requests, successful_requests, failed_requests
        try:
            req = urllib.request.Request(
                full_url,
                headers={"User-Agent": "HPA-Load-Generator/1.0", "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                code = resp.getcode()
                if 200 <= code < 400:
                    successful_requests += 1
                else:
                    failed_requests += 1
        except Exception:
            failed_requests += 1
        total_requests += 1

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        active_futures = set()
        for _ in range(concurrency * 2):
            active_futures.add(executor.submit(fetch))

        while not stop_requested:
            done = {f for f in active_futures if f.done()}
            active_futures -= done
            for _ in range(len(done)):
                if not stop_requested:
                    active_futures.add(executor.submit(fetch))

            now = time.time()
            if now - last_report_time >= 5.0:
                elapsed = now - start_time
                rate = total_requests / elapsed if elapsed > 0 else 0
                print(
                    f"[{time.strftime('%H:%M:%S')}] Elapsed: {int(elapsed):3d}s | "
                    f"Sent: {total_requests:5d} reqs | "
                    f"Throughput: {rate:5.1f} req/s | "
                    f"200 OK: {successful_requests:5d} | "
                    f"Errors: {failed_requests:3d}"
                )
                last_report_time = now
            time.sleep(0.01)

    elapsed_total = time.time() - start_time
    avg_rate = total_requests / elapsed_total if elapsed_total > 0 else 0
    print("\n" + "=" * 70)
    print("🛑 LOAD TEST STOPPED BY USER (Ctrl+C)")
    print("=" * 70)
    print(f"Total Duration     : {elapsed_total:.1f} seconds")
    print(f"Total Requests     : {total_requests}")
    print(f"Successful (2xx)   : {successful_requests}")
    print(f"Failed / Errors    : {failed_requests}")
    print(f"Average Throughput : {avg_rate:.1f} req/s")
    print("=" * 70)
    print("👉 Now observe automatic HPA scale-down via:")
    print("   kubectl get hpa backend-hpa -n healthcare -w")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kubernetes HPA Load Generator")
    parser.add_argument(
        "--target-url",
        type=str,
        default=os.getenv("TARGET_URL", "http://85.211.219.5"),
        help="Target base URL (default: http://85.211.219.5 or TARGET_URL env var)"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default=os.getenv("TARGET_ENDPOINT", "/api/v1/doctors"),
        help="Target API endpoint (default: /api/v1/doctors)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=int(os.getenv("CONCURRENCY", "25")),
        help="Number of concurrent worker threads (default: 25)"
    )
    args = parser.parse_args()

    run_load_test(
        target_url=args.target_url,
        endpoint=args.endpoint,
        concurrency=args.concurrency
    )

import os
import uuid
import argparse
import threading
import concurrent.futures
from fastapi.testclient import TestClient
from backend.app.main import app

def test_prevent_double_booking_concurrent_requests(target_url: str = None):
    """
    Fire 10 concurrent requests to book the exact same doctor slot.
    Assert that exactly ONE request succeeds (201 Created)
    and all 9 other concurrent attempts receive 409 Conflict.
    Can run against in-process FastAPI TestClient or live cluster URL.
    The target URL can be passed via argument, CLI, or API_BASE_URL/TARGET_URL env vars.
    """
    target_url = target_url or os.getenv("API_BASE_URL") or os.getenv("TARGET_URL")
    if target_url:
        target_url = target_url.rstrip("/")

    use_remote = bool(target_url)
    
    unique_tag = uuid.uuid4().hex[:6]
    tag_int = int(unique_tag, 16)
    month = (tag_int % 12) + 1
    day = (tag_int % 28) + 1
    booking_date = f"2027-{month:02d}-{day:02d}"
    slot_time = "10:00"
    num_concurrent_requests = 10

    # Barrier to synchronize all worker threads so they release and fire simultaneously
    barrier = threading.Barrier(num_concurrent_requests)

    def attempt_booking(idx: int):
        payload = {
            "doctor_id": "doc_1",
            "patient_id": f"pat_{unique_tag}_{idx}",
            "date": booking_date,
            "start_time": slot_time,
            "end_time": "10:30"
        }
        # Synchronize all threads before firing
        barrier.wait()
        if use_remote:
            import httpx
            with httpx.Client(base_url=target_url, timeout=15.0) as client:
                return client.post("/api/v1/appointments", json=payload)
        else:
            c = TestClient(app)
            return c.post("/api/v1/appointments", json=payload)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
        futures = [executor.submit(attempt_booking, i) for i in range(num_concurrent_requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    status_codes = [r.status_code for r in results]
    success_responses = [r for r in results if r.status_code == 201]
    conflict_responses = [r for r in results if r.status_code == 409]

    print(f"\n[CONCURRENCY AUDIT] Target: {target_url or 'In-Process TestClient'}")
    print(f"[CONCURRENCY AUDIT] Doctor: doc_1 | Date: {booking_date} | Time: {slot_time}")
    print(f"[CONCURRENCY AUDIT] Total requests fired concurrently: {num_concurrent_requests}")
    print(f"[CONCURRENCY AUDIT] Received HTTP Status Codes: {status_codes}")
    print(f"[CONCURRENCY AUDIT] Successful bookings (201 Created): {len(success_responses)}")
    print(f"[CONCURRENCY AUDIT] Blocked race conditions (409 Conflict): {len(conflict_responses)}")

    assert len(success_responses) == 1, f"Expected 1 success, got {len(success_responses)} (codes: {status_codes})"
    assert len(conflict_responses) == num_concurrent_requests - 1, f"Expected {num_concurrent_requests - 1} conflicts, got {len(conflict_responses)}"

    # Verify audit log verification
    if use_remote:
        import httpx
        with httpx.Client(base_url=target_url, timeout=10.0) as client:
            audit_res = client.get("/api/v1/audit/events")
            assert audit_res.status_code == 200
            events = audit_res.json()
            conflicts = [e for e in events if e.get("event_type") == "CONFLICT_PREVENTED"]
            assert len(conflicts) >= 1
    else:
        client = TestClient(app)
        audit_res = client.get("/api/v1/audit/events")
        assert audit_res.status_code == 200
        events = audit_res.json()
        conflicts = [e for e in events if e.get("event_type") == "CONFLICT_PREVENTED"]
        assert len(conflicts) >= 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live Cluster Concurrency Test")
    parser.add_argument("--target-url", type=str, default=None, help="Cluster or Ingress URL (e.g. http://<IP>)")
    args = parser.parse_args()
    resolved_url = args.target_url or os.getenv("API_BASE_URL") or os.getenv("TARGET_URL") or "http://localhost:8000"
    print(f"Running multi-replica concurrency test against: {resolved_url}")
    test_prevent_double_booking_concurrent_requests(target_url=resolved_url)
    print("✓ Concurrency invariant verified: 1 Created, 9 Rejected with 409 Conflict.")

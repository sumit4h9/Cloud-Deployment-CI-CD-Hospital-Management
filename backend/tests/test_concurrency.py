import uuid
import sys
import argparse
import concurrent.futures
from fastapi.testclient import TestClient
from backend.app.main import app

def test_prevent_double_booking_concurrent_requests(target_url: str = None):
    """
    Fire multiple concurrent requests to book the exact same doctor slot.
    Assert that exactly ONE request succeeds (201 Created)
    and all other concurrent attempts receive 409 Conflict.
    Can run against in-process FastAPI TestClient or live cluster URL.
    """
    use_remote = bool(target_url)
    
    unique_tag = uuid.uuid4().hex[:6]
    booking_date = f"2027-{unique_tag[:2]}-01"
    slot_time = "10:00"
    num_concurrent_requests = 10

    def attempt_booking(idx: int):
        payload = {
            "doctor_id": "doc_1",
            "patient_id": f"pat_{unique_tag}_{idx}",
            "date": booking_date,
            "start_time": slot_time,
            "end_time": "10:30"
        }
        if use_remote:
            import httpx
            with httpx.Client(base_url=target_url, timeout=10.0) as client:
                return client.post("/api/v1/appointments", json=payload)
        else:
            c = TestClient(app)
            return c.post("/api/v1/appointments", json=payload)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
        futures = [executor.submit(attempt_booking, i) for i in range(num_concurrent_requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_responses = [r for r in results if r.status_code == 201]
    conflict_responses = [r for r in results if r.status_code == 409]

    print(f"\n[CONCURRENCY AUDIT] Total requests fired: {num_concurrent_requests}")
    print(f"[CONCURRENCY AUDIT] Successful bookings (201 Created): {len(success_responses)}")
    print(f"[CONCURRENCY AUDIT] Blocked race conditions (409 Conflict): {len(conflict_responses)}")

    assert len(success_responses) == 1, f"Expected 1 success, got {len(success_responses)} (codes: {[r.status_code for r in results]})"
    assert len(conflict_responses) == num_concurrent_requests - 1

    # Verify audit log verification
    if use_remote:
        import httpx
        with httpx.Client(base_url=target_url, timeout=5.0) as client:
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
    parser.add_argument("--target-url", type=str, default="http://localhost:8000", help="Cluster or Ingress URL")
    args = parser.parse_args()
    print(f"Running multi-replica concurrency test against: {args.target_url}")
    test_prevent_double_booking_concurrent_requests(target_url=args.target_url)
    print("✓ Concurrency invariant verified: 1 Created, 9 Rejected with 409 Conflict.")

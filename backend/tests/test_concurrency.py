import uuid
import concurrent.futures
from fastapi.testclient import TestClient
from backend.app.main import app

def test_prevent_double_booking_concurrent_requests():
    """
    Fire multiple concurrent requests to book the exact same doctor slot.
    Assert that exactly ONE request succeeds (201 Created)
    and all other concurrent attempts receive 409 Conflict.
    """
    client = TestClient(app)

    # Use a unique date so tests are idempotent and can be run repeatedly
    unique_tag = uuid.uuid4().hex[:6]
    booking_date = f"2027-01-01"
    slot_time = "10:00"
    num_concurrent_requests = 10

    def attempt_booking(idx: int):
        c = TestClient(app)
        payload = {
            "doctor_id": "doc_1",
            "patient_id": f"pat_{unique_tag}_{idx}",
            "date": f"2027-{unique_tag[:2]}-01",
            "start_time": slot_time,
            "end_time": "10:30"
        }
        return c.post("/api/v1/appointments", json=payload)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
        futures = [executor.submit(attempt_booking, i) for i in range(num_concurrent_requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_responses = [r for r in results if r.status_code == 201]
    conflict_responses = [r for r in results if r.status_code == 409]

    assert len(success_responses) == 1, f"Expected 1 success, got {len(success_responses)} (codes: {[r.status_code for r in results]})"
    assert len(conflict_responses) == num_concurrent_requests - 1

    # Check audit logs recorded CONFLICT_PREVENTED
    audit_res = client.get("/api/v1/audit?event_type=CONFLICT_PREVENTED")
    assert audit_res.status_code == 200
    conflicts = audit_res.json()
    assert len(conflicts) >= 1

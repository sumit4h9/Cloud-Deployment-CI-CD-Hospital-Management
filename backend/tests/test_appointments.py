import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_list_doctors():
    response = client.get("/api/v1/doctors")
    assert response.status_code == 200
    doctors = response.json()
    assert len(doctors) >= 1
    ananya = next((d for d in doctors if "Ananya" in d["name"]), None)
    assert ananya is not None
    assert ananya["specialization"] == "Cardiology"

def test_list_slots_and_appointments():
    # Verify Dr. Ananya's slots on 2026-11-06
    slots_res = client.get("/api/v1/doctors/doc_1/slots?date=2026-11-06")
    assert slots_res.status_code == 200
    slots = slots_res.json()
    assert len(slots) >= 7

    # Verify appointments
    apts_res = client.get("/api/v1/appointments?doctor_id=doc_1&date=2026-11-06")
    assert apts_res.status_code == 200
    apts = apts_res.json()
    assert len(apts) >= 1

def test_appointment_lifecycle():
    # 1. Book an available slot at 10:00 AM
    create_payload = {
        "doctor_id": "doc_1",
        "patient_id": "pat_test_99",
        "date": "2026-11-06",
        "start_time": "10:00",
        "end_time": "10:30"
    }
    create_res = client.post("/api/v1/appointments", json=create_payload)
    assert create_res.status_code == 201
    apt = create_res.json()
    apt_id = apt["id"]
    assert apt["status"] == "Confirmed"
    assert apt["doctor_name"] == "Dr. Ananya Mehta"

    # 2. Reschedule to 11:30 AM
    reschedule_payload = {
        "new_date": "2026-11-06",
        "new_start_time": "11:30",
        "new_end_time": "12:00"
    }
    resched_res = client.patch(f"/api/v1/appointments/{apt_id}/reschedule", json=reschedule_payload)
    assert resched_res.status_code == 200
    assert resched_res.json()["status"] == "Rescheduled"
    assert resched_res.json()["start_time"] == "11:30"

    # 3. Cancel the appointment
    cancel_res = client.post(f"/api/v1/appointments/{apt_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "Cancelled"

    # 4. Verify slot is released (11:30 should be available again)
    slots_res = client.get("/api/v1/doctors/doc_1/slots?date=2026-11-06")
    slot_1130 = next((s for s in slots_res.json() if s["start_time"] == "11:30"), None)
    if slot_1130:
        assert slot_1130["is_available"] is True

def test_invalid_doctor_reference():
    payload = {
        "doctor_id": "invalid_doc_999",
        "patient_id": "pat_1014",
        "date": "2026-11-06",
        "start_time": "12:00"
    }
    res = client.post("/api/v1/appointments", json=payload)
    assert res.status_code == 400


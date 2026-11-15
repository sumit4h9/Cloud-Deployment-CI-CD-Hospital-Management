from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_portal_login_doctor():
    res = client.post("/api/v1/auth/login", json={
        "portal": "doctor",
        "identifier": "doc_1"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "doctor"
    assert data["user"]["name"] == "Dr. Ananya Mehta"
    assert "token" in data["access_token"]

def test_portal_login_patient():
    res = client.post("/api/v1/auth/login", json={
        "portal": "patient",
        "identifier": "1042"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "patient"
    assert "1042" in data["user"]["name"]

def test_portal_login_admin():
    res = client.post("/api/v1/auth/login", json={
        "portal": "admin",
        "identifier": "admin_1"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "admin"
    assert "Administrator" in data["user"]["name"]

def test_role_authorization_doctor_vs_patient():
    # As doctor
    doc_res = client.get("/api/v1/appointments?doctor_id=doc_1", headers={"Authorization": "Bearer doctor-ananya"})
    assert doc_res.status_code == 200

    # As patient
    pat_res = client.get("/api/v1/appointments?patient_id=pat_1042", headers={"Authorization": "Bearer patient-1042"})
    assert pat_res.status_code == 200
    for apt in pat_res.json():
        assert apt["patient_id"] == "pat_1042"

def test_invalid_login_credentials():
    res = client.post("/api/v1/auth/login", json={
        "portal": "doctor",
        "identifier": "nonexistent_doctor",
        "password": "wrong_password"
    })
    assert res.status_code == 401
    assert "Invalid credentials" in res.json()["detail"]



# Doctor Appointment Scheduling Platform & API

A focused, production-grade appointment management platform designed strictly within the required assessment scope: **a doctor appointment scheduling service using synthetic patient data**, avoiding the visual noise and excessive clinical complexity of full EMR/EHR software.

---

## 🎯 Design Philosophy: Real Product vs. AI-Generated EMR

| Previous AI-Generated Prototype | Redesigned Realistic Product |
| :--- | :--- |
| **Noise & Density**: 20+ tiny metadata pills, audit cycles, session timeouts (`SEC-AUD-4491`), hospital census | **40% Density Reduction**: Clear typography, focused hierarchy, only elements that help schedule/reschedule/cancel |
| **Invented Clinical Details**: Vitals, prescriptions, fake diagnoses, ECG reviews, chart sign-offs | **Appointment-Focused**: Time, Patient ID, Status, Action (`View`, `Reschedule`, `Cancel`) |
| **Fake Enterprise Complexities**: HIPAA barriers, OR allocation, hyperspace console IDs | **Clean Healthcare Aesthetic**: Light neutral background, dark charcoal text, restrained healthcare blue/teal (`#0284C7`) |
| **Blurred Roles**: Jumbled clinical admin, doctor, patient, and IT console controls | **Role-Specific Views**: Dedicated Doctor Portal (`Dr. Ananya Mehta`) and Patient Portal (`Patient #1042`) |

---

## 🩺 System Capabilities & Assessment Scope

1. **Service**: Doctor Appointment API.
2. **Health & Readiness Endpoints**:
   - `GET /health`: Liveness probe (`{"status": "healthy"}`).
   - `GET /ready`: Readiness probe verifying database connectivity (`{"status": "ready", "database": "connected"}`).
3. **Doctor & Slot Management**:
   - List doctors, filter by specialization and date.
   - List doctor slots with availability status (`Available` or `Booked`).
   - Doctor ability to add or toggle availability (`[Add Slot]`, `[Disable Slot]`).
4. **Appointment Lifecycle**:
   - Create, reschedule, and cancel appointments.
   - Validation for doctor/patient existence and time window boundaries.
5. **Concurrency & Race Condition Protection**:
   - Atomic reservation lock preventing double-booking of the same doctor/time slot under concurrent requests.
   - Verified via automated test firing 10 concurrent requests simultaneously; guarantees exactly 1 success (`201 Created`) and 9 conflicts (`409 Conflict`).
6. **Audit Events**:
   - Structured audit logging for all scheduling actions (`APPOINTMENT_CREATED`, `APPOINTMENT_RESCHEDULED`, `APPOINTMENT_CANCELLED`, `CONFLICT_PREVENTED`).
7. **Synthetic Seed Data**:
   - Preloaded with `Dr. Ananya Mehta` (Cardiology), `Patient #1014`, `Patient #1029`, `Patient #1042`, etc., matching the exact schedule state.

---

## 🚀 Quick Start

### 1. Run the Backend API

```powershell
# Run API server (auto-seeds database)
uvicorn backend.app.main:app --reload --port 8000
```
- Interactive API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)
- Readiness Probe: [http://localhost:8000/ready](http://localhost:8000/ready)

### 2. Run the Frontend UI

```powershell
cd frontend
npm install
npm run dev
```
- Open browser at: [http://localhost:5173](http://localhost:5173)
- Use the **Role Switcher** in the top header to toggle between **Doctor Portal** and **Patient Portal**.

---

## 🧪 Automated Test Suite

Run the full pytest suite:

```powershell
python -m pytest backend/tests -v
```

### Test Coverage Summary:
- `test_health.py`: Verifies `/health` and `/ready` probes.
- `test_appointments.py`: Verifies doctor lookup, slot availability, appointment creation, rescheduling, cancellation, and slot restoration.
- `test_concurrency.py`: Verifies concurrency safety under concurrent thread load, ensuring no double-booking and checking audit records.
- `test_auth.py`: Verifies doctor and patient role access.

---

## 🐳 Docker & Production Deployment

Run via Docker Compose:

```bash
docker compose up --build
```
Healthcheck is configured to verify container status via `curl http://localhost:8000/health`.


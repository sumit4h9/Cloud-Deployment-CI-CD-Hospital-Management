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

### One-Command Launch (Tests + Build + Server)

**Windows (PowerShell):**
```powershell
.\run.ps1
```

**Linux / macOS:**
```bash
chmod +x run.sh
./run.sh
```

This command automatically:
1. Executes all 10 automated concurrency and API tests.
2. Builds the clean production frontend bundle.
3. Launches the unified server on `http://localhost:8000`.

---

## 🔐 Role-Specific Portals & Access

| Portal | Intended User | Default Credential Preset | Capabilities |
| :--- | :--- | :--- | :--- |
| **Doctor Portal** | Physicians & Clinical Staff | `ananya.mehta@clinic.local` / `doc_1` | View daily schedule, 3 clean metrics, today's appointments list, reschedule/cancel modal, and dedicated availability slot management (`[Add Slot]`, `[Disable Slot]`). |
| **Patient Portal** | Patients (Synthetic) | `Patient #1042` / `1042` | View personal upcoming appointment card, search specialists, and follow a 4-step slot reservation workflow. |

---

## 🌐 Endpoints & Web Access

- **Web Application**: [http://localhost:8000](http://localhost:8000) (Portal gateway)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check (Liveness)**: [http://localhost:8000/health](http://localhost:8000/health)
- **Readiness Probe**: [http://localhost:8000/ready](http://localhost:8000/ready)

### Separate Dev Server (Optional)
If running Vite with Hot Module Replacement (HMR) for frontend development:
```powershell
# Terminal 1: Backend
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```
Open [http://localhost:5173](http://localhost:5173).

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


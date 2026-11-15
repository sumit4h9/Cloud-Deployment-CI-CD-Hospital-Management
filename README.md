# Healthcare Management Platform — Doctor Appointment System

A high-reliability, production-grade appointment management platform designed strictly within the required assignment scope: **a doctor appointment scheduling service using synthetic patient data**, avoiding the visual noise and excessive clinical complexity of full EMR/EHR software.

---

## 🎯 Architecture Overview

```
                                  TRAFFIC / USERS
                                         │
                                         ▼
                            Ingress: clinic-ingress
                     ┌───────────────────┴───────────────────┐
                     │ (path: /)                             │ (path: /api, /health, /metrics)
                     ▼                                       ▼
             frontend-service                        backend-service
                     │                                       │
            ┌────────┴────────┐                     ┌────────┼────────┐
            ▼                 ▼                     ▼        ▼        ▼
       Frontend Pod 1    Frontend Pod 2          Backend  Backend  Backend
        (Nginx SPA)       (Nginx SPA)             Pod 1    Pod 2    Pod 3...
                                                    │        │        │
                                                    └────────┼────────┘
                                                             │
                                   ┌─────────────────────────┴─────────────────────────┐
                                   ▼                                                   ▼
                          postgres-service                                     worker-deployment
                       (Headless StatefulSet)                                  (Background Jobs)
                                   │
                           postgres-storage
                                (PVC)
```

---

## 🩺 System Capabilities & Core Contracts

1. **Healthcare Service Scope**: Doctor Appointment API & Multi-Role Web Portal.
2. **Health, Readiness & Metrics Endpoints**:
   - `GET /health`: Liveness probe (`{"status": "healthy", "service": "doctor-appointment-api", "version": "1.0.0"}`). Never fails when the database is restarting.
   - `GET /ready`: Readiness probe verifying active database connectivity (`SELECT 1`). Fails with HTTP 503 if the database is temporarily unavailable, cleanly removing the pod from service endpoints.
   - `GET /metrics`: Prometheus telemetry metrics covering HTTP traffic, domain bookings, cancellations, and prevented concurrency conflicts.
3. **Role-Based Portals (RBAC)**:
   - **Doctor Portal**: Daily schedule, 3 clean focus metrics, today's appointments list, appointment completion action (`[Mark as Completed]`), rescheduling, and bookable availability slot management (`[+ Add Slot]`, `[Disable Slot]`).
   - **Patient Portal**: Upcoming appointment card (`#APT-10482`), specialist search, and self-service slot booking workflow.
   - **Admin / Operations Portal**: Clinic overview, doctor roster & suite inspector, master appointments register, live security & scheduling audit stream, and probe telemetry contracts.
4. **Database-Level Concurrency Protection (Multi-Replica Safe)**:
   - In-memory locks were eliminated in favor of database-level invariants.
   - **Partial Unique Index**: `CREATE UNIQUE INDEX uq_active_appointment ON appointments (doctor_id, date, start_time) WHERE status IN ('Confirmed', 'Rescheduled');`
   - **Atomic Conditional Slot Claim**: `UPDATE slots SET is_available = False WHERE id = :id AND is_available = True`
   - Simultaneous conflicting requests trigger database integrity rollback, record `CONFLICT_PREVENTED` in the audit log, increment Prometheus counters, and return `HTTP 409 Conflict`.
   - Verified via automated concurrency test firing 10 simultaneous threads: exactly 1 booking succeeds (`201 Created`) and 9 are rejected (`409 Conflict`).

---

## 🚀 Local Deployment Runbook

### 1. Docker Compose (Full 6-Container Microservice Stack)

```bash
# Build and launch all services in background
docker compose up -d --build

# Verify container health status
docker compose ps
```

**Exposed Services:**
- Frontend Web Portal: [http://localhost:80](http://localhost:80)
- Backend REST API & Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Prometheus Telemetry: [http://localhost:9090](http://localhost:9090)
- Grafana Observability Dashboards: [http://localhost:3000](http://localhost:3000) (User: `admin` / Password: `admin`)
- PostgreSQL Persistence: `localhost:5432` (`postgres_data` persistent volume)

---

### 2. Kubernetes Local Deployment (Minikube / K3s)

All manifests in `k8s/` are bundled via Kustomize:

```bash
# 1. Preview and validate manifests
kubectl kustomize k8s/

# 2. Deploy the complete stack to namespace 'healthcare'
kubectl apply -k k8s/

# 3. Verify deployed workloads and pods
kubectl get all,hpa,pvc,ingress -n healthcare
```

#### Workloads Deployed:
- `postgres` (StatefulSet + 2Gi PVC `postgres-storage`): Persistent database with headless service `postgres-service`.
- `backend-deployment` (Deployment): Stateless API with 2 baseline replicas (autoscales up to 6 via HPA).
- `frontend-deployment` (Deployment): 2 replicas of the Nginx SPA reverse-proxying API traffic.
- `worker-deployment` (Deployment): 1 replica running the background job scheduler (reminders, expired slot reclamation).
- `backend-hpa` (HorizontalPodAutoscaler): Scales backend pods from 2 to 6 based on CPU utilization (> 70%) and memory (> 80%).
- `prometheus-deployment` & `grafana-deployment`: Local cluster observability stack.
- `clinic-ingress` (Ingress): Ingress controller routing `/` to frontend and `/api`, `/health`, `/metrics` to backend.

---

## 📈 Horizontal Pod Autoscaling (HPA)

The backend autoscaler is configured under `autoscaling/v2`:

```yaml
minReplicas: 2
maxReplicas: 6
metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### HPA Scaling Verification:
```bash
# 1. Inspect current HPA status
kubectl get hpa backend-hpa -n healthcare

# 2. Simulate load spike
kubectl run load-generator --image=busybox --restart=Never -n healthcare -- /bin/sh -c "
  while true; do wget -q -O- http://backend-service:8000/api/v1/doctors; done
"

# 3. Observe scaling from 2 -> 4 -> 6 replicas
kubectl get hpa backend-hpa -n healthcare -w

# 4. Stop load and observe stabilized scale down
kubectl delete pod load-generator -n healthcare
```

---

## 🛡️ Resilience & Failure Recovery Procedures

### 1. Pod Failure & Self-Healing
If any backend or frontend pod crashes or is terminated:
```bash
# Terminate a backend pod
kubectl delete pod -l app=backend -n healthcare --now

# Observe immediate self-healing
kubectl get pods -n healthcare -l app=backend -w
```
Kubernetes detects missing replica count, creates a replacement pod, runs readiness checks, and restores full capacity.

### 2. Database Outage & Readiness Isolation
```bash
# Temporarily scale down PostgreSQL
kubectl scale statefulset postgres --replicas=0 -n healthcare

# Query readiness probe
curl -i http://localhost:8000/ready
# Returns HTTP 503 Service Unavailable (Liveness probe /health remains 200 OK)

# Restore PostgreSQL
kubectl scale statefulset postgres --replicas=1 -n healthcare

# Query readiness probe
curl -i http://localhost:8000/ready
# Returns HTTP 200 OK
```

### 3. Application Rollout & Zero-Downtime Rollback
```bash
# View rollout history
kubectl rollout history deployment/backend-deployment -n healthcare

# If a bad deployment occurs:
kubectl rollout undo deployment/backend-deployment -n healthcare

# Check status of rollback
kubectl rollout status deployment/backend-deployment -n healthcare
```

---

## 💾 Database Backup & Restore Procedure

PostgreSQL-native backups use `pg_dump` and `pg_restore` with synthetic data.

### To take a backup:
```bash
# Linux / macOS / Bash:
./scripts/backup.sh

# Windows (PowerShell):
.\scripts\backup.ps1
```

### To restore a backup:
```bash
# Linux / macOS / Bash:
./scripts/restore.sh ./backups/postgres_k8s_20261115_120000.dump

# Windows (PowerShell):
.\scripts\restore.ps1 -BackupFile "./backups/postgres_k8s_20261115_120000.dump"
```

---

## 🧪 Automated Test Suite

Run the full pytest suite (15 unit and integration tests):

```bash
python -m pytest backend/tests -v
```

### Test Coverage:
- `test_health.py`: Liveness (`/health`), readiness probe isolation (`/ready`), and Prometheus telemetry (`/metrics`).
- `test_appointments.py`: Doctor directory, availability slots, appointment lifecycle (create, reschedule, cancel, complete), invalid doctor reference handling, and clinic operating hours validation (08:00 - 18:00).
- `test_auth.py`: Role-based authentication (Doctor, Patient, Admin) and invalid credential rejection.
- `test_concurrency.py`: Database-level mutual exclusion test firing 10 concurrent requests simultaneously; guarantees exactly 1 success (`201 Created`) and 9 conflicts (`409 Conflict`).

---

## 🔒 Security & Trivy Scanning

Run Trivy container and filesystem vulnerability scan locally:

```bash
make scan
```
Or in GitHub Actions: `.github/workflows/ci.yml` automatically scans both Docker images and dependencies for `CRITICAL` and `HIGH` CVEs on every commit and pull request.

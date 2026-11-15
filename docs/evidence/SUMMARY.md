# Local Engineering & Verification Evidence Log
**Project:** ALGIONS AI Labs — Hospital Appointment Management Platform  
**Environment:** Local Kubernetes (Minikube/K3s) & Docker Compose  
**Date:** November 2026  

---

## Acceptance Verification Index

| ID | Checkpoint / Test Item | Command / Mechanism | Status | Evidence Document |
| :--- | :--- | :--- | :---: | :--- |
| **01** | Docker Compose Stack | `docker compose config` (6 services) | **PASS** | [01-compose.md](01-compose.md) |
| **02** | Kubernetes Manifests | `kubectl kustomize k8s/` | **PASS** | [02-kubernetes.md](02-kubernetes.md) |
| **03** | Health & Readiness | `GET /health` (200) vs `GET /ready` (200/503) | **PASS** | [03-health-readiness.md](03-health-readiness.md) |
| **04** | HPA Autoscaling | `backend-hpa` (2 ➔ 6 pods, CPU > 70%) | **PASS** | [04-hpa.md](04-hpa.md) |
| **05** | Prometheus Telemetry | `GET /metrics` custom app counters | **PASS** | [05-prometheus.md](05-prometheus.md) |
| **06** | Grafana Dashboards | Datasource + `clinic_overview.json` | **PASS** | [06-grafana.md](06-grafana.md) |
| **07** | Concurrency Protection | 10 concurrent requests: 1 Success, 9 Conflicts | **PASS** | [07-concurrency.md](07-concurrency.md) |
| **08** | Backend Pod Recovery | `kubectl delete pod` (automatic recreation) | **PASS** | [08-backend-recovery.md](08-backend-recovery.md) |
| **09** | Frontend Pod Recovery | Ingress traffic continuity + replacement pod | **PASS** | [09-frontend-recovery.md](09-frontend-recovery.md) |
| **10** | Worker Recovery | Single active replica scheduler recovery | **PASS** | [10-worker-recovery.md](10-worker-recovery.md) |
| **11** | Database Recovery | DB stop ➔ `/ready` 503 ➔ DB restart ➔ 200 | **PASS** | [11-database-recovery.md](11-database-recovery.md) |
| **12** | Backup & Restore | `scripts/backup.ps1` & `scripts/restore.ps1` | **PASS** | [12-backup-restore.md](12-backup-restore.md) |
| **13** | Kubernetes Rollback | `kubectl rollout undo deployment/backend-deployment` | **PASS** | [13-rollback.md](13-rollback.md) |
| **14** | Trivy Security Scan | `make scan` + `.github/workflows/ci.yml` | **PASS** | [14-trivy.md](14-trivy.md) |
| **15** | CI Pipeline | GitHub Actions Python + Node + Trivy | **PASS** | [15-ci.md](15-ci.md) |

---

## Key Reliability Invariants Proven

1. **Database-Level Mutual Exclusion**:
   - `uq_active_appointment` partial unique index on `appointments` table:
     `WHERE status IN ('Confirmed', 'Rescheduled')`
   - Atomic conditional slot update:
     `UPDATE slots SET is_available = False WHERE id = :id AND is_available = True`
   - Under simultaneous concurrent race conditions across multiple pods, exactly 1 booking commits (`201 Created`) and all other competing requests receive `409 Conflict`.
2. **Readiness vs Liveness Independence**:
   - `GET /health` reports container process status without external dependencies.
   - `GET /ready` isolates service endpoints if PostgreSQL is temporarily restarting or unready.
3. **Persistent State Guarantee**:
   - PostgreSQL runs as a Kubernetes `StatefulSet` with headless `postgres-service` and dynamic persistent volume claims (`postgres-storage` 2Gi `ReadWriteOnce`).


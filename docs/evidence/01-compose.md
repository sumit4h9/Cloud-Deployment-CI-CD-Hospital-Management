# Evidence 01: Docker Compose Stack Verification

```bash
$ docker compose config
```

### Verified Service Architecture:
1. `backend`: FastAPI API server (Port 8000, connected to database, healthcheck on `/health`).
2. `database`: PostgreSQL 16 Alpine (Port 5432, volume `postgres_data`, healthcheck `pg_isready`).
3. `frontend`: Nginx React SPA (Port 80, reverse proxies API and health routes, healthcheck via `wget`).
4. `worker`: Scheduled background operational worker (appointment reminders, slot reclamation).
5. `monitoring`: Prometheus v2.51.0 (Port 9090, volume `prometheus_data`, scrapes backend `/metrics`).
6. `grafana`: Grafana v10.4.1 (Port 3000, volume `grafana_data`, auto-provisioned Prometheus datasource & dashboards).

All services reside in an isolated bridge network `clinic-network` with health-based startup dependencies.
Status: **PASS**


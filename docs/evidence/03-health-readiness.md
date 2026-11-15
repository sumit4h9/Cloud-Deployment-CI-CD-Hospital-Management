# Evidence 03: Health, Readiness & Metrics Probe Separation

## 1. Live Kubernetes Cluster Probe Validation

```bash
$ curl -s http://backend-service:8000/health
$ curl -s http://backend-service:8000/ready
$ curl -s http://backend-service:8000/metrics
```

### Live Responses:

1. **Liveness Probe (`GET /health`)**:
```json
{
  "status": "healthy",
  "service": "doctor-appointment-api",
  "version": "1.0.0"
}
```

2. **Readiness Probe (`GET /ready`) - Healthy State**:
```json
{
  "status": "ready",
  "database": "connected"
}
```

3. **Prometheus Metrics Endpoint (`GET /metrics`)**:
```text
# HELP appointment_requests_total Total number of appointment requests
# TYPE appointment_requests_total counter
appointment_requests_total{status="201"} 13.0
appointment_requests_total{status="409"} 9.0

# HELP appointment_conflicts_total Total number of double-booking race condition conflicts prevented
# TYPE appointment_conflicts_total counter
appointment_conflicts_total 9.0
```

---

## 2. Monitoring & Observability Stack

- **Prometheus Server**: `http://prometheus-service:9090/-/healthy`
  - Output: `Prometheus Server is Healthy.`
  - Target Status (`http://prometheus-service:9090/api/v1/targets`):
    - `job="doctor-appointment-backend"`
    - `instance="backend-service:8000"`
    - `health="up"` (Scrape interval: 15s)
- **Grafana Server**: `http://grafana-service:3000/api/health`
  - Output:
    ```json
    {
      "commit": "d94d597d847c05085542c29dfad6b3f469cc77e1",
      "database": "ok",
      "version": "10.4.1"
    }
    ```

**Status**: **PASS**

# Evidence 03: Health, Readiness & Metrics Probe Separation

### Probe Contract Verification:

1. **Liveness Probe (`GET /health`)**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "service": "doctor-appointment-api",
  "version": "1.0.0"
}
```
*Behavior*: Tests process health independently. Never fails due to external database restarts.

2. **Readiness Probe (`GET /ready`) - Healthy State**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ready",
  "database": "connected"
}
```

3. **Readiness Probe (`GET /ready`) - Database Unavailable State**:
```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "detail": "Database readiness failed: connection refused"
}
```
*Behavior*: Isolates pod from Kubernetes Service endpoint routing without triggering an unnecessary restart loop.

Status: **PASS**


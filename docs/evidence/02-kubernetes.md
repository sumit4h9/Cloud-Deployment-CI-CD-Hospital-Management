# Evidence 02: Kubernetes Manifests & Kustomize Validation

```bash
$ kubectl kustomize k8s/
```

### Verified Manifest Resources in namespace `healthcare`:
- `Namespace`: `healthcare`
- `ConfigMap`: `clinic-config`, `prometheus-config`, `grafana-datasources`
- `Secret`: `clinic-secrets` (Opaque: `POSTGRES_PASSWORD`, `JWT_SECRET`)
- `Service`:
  - `backend-service`: ClusterIP on port 8000
  - `frontend-service`: ClusterIP on port 80
  - `postgres-service`: Headless (clusterIP: None) on port 5432
  - `prometheus-service`: ClusterIP on port 9090
  - `grafana-service`: ClusterIP on port 3000
- `StatefulSet`: `postgres` (1 replica, PVC `postgres-storage` 2Gi)
- `Deployment`:
  - `backend-deployment`: 2 replicas base (HPA target)
  - `frontend-deployment`: 2 replicas
  - `worker-deployment`: 1 replica
  - `prometheus-deployment`: 1 replica
  - `grafana-deployment`: 1 replica
- `HorizontalPodAutoscaler`: `backend-hpa` (2 to 6 replicas)
- `Ingress`: `clinic-ingress` (Nginx ingress class, routing `/` to frontend, `/api` & probes to backend)

Status: **PASS**


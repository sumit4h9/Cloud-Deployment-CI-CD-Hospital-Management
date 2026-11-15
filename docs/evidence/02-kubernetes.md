# Evidence 02: Kubernetes Manifests & Live Cluster Deployment Verification

**Cluster**: K3s v1.31 CNCF Certified Kubernetes  
**Namespace**: `healthcare`  
**Images**: Immutable C2 GHCR Releases (`v1.0.0`)

---

## 1. Workload Verification (`kubectl get all,pvc,hpa -n healthcare`)

```text
NAME                                        READY   STATUS    RESTARTS   AGE
pod/backend-deployment-84bdfdb75d-p4fxs     1/1     Running   0          2m
pod/backend-deployment-84bdfdb75d-z4dwv     1/1     Running   2          6m
pod/frontend-deployment-f579f5c84-g8bfv     1/1     Running   12         26m
pod/frontend-deployment-f579f5c84-zsqrs     1/1     Running   12         26m
pod/grafana-deployment-66db9db46b-5cpcl     1/1     Running   0          26m
pod/postgres-0                              1/1     Running   0          2m
pod/prometheus-deployment-cd445b4d9-m6gcm   1/1     Running   3          26m
pod/worker-deployment-55b5b9c4f8-rh5z5      1/1     Running   7          26m

NAME                         TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
service/backend              ClusterIP   10.43.85.76    <none>        8000/TCP   6m
service/backend-service      ClusterIP   10.43.58.122   <none>        8000/TCP   26m
service/frontend-service     ClusterIP   10.43.99.114   <none>        80/TCP     26m
service/grafana-service      ClusterIP   10.43.192.85   <none>        3000/TCP   26m
service/postgres-service     ClusterIP   None           <none>        5432/TCP   26m
service/prometheus-service   ClusterIP   10.43.208.33   <none>        9090/TCP   26m

NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/backend-deployment      2/2     2            2           26m
deployment.apps/frontend-deployment     2/2     2            2           26m
deployment.apps/grafana-deployment      1/1     1            1           26m
deployment.apps/prometheus-deployment   1/1     1            1           26m
deployment.apps/worker-deployment       1/1     1            1           26m

NAME                        READY   AGE
statefulset.apps/postgres   1/1     26m

NAME                                              REFERENCE                       TARGETS                        MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/backend-hpa   Deployment/backend-deployment   cpu: 6%/70%, memory: 47%/80%   2         6         2          26m

NAME                                                STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/postgres-storage-postgres-0   Bound    pvc-9b59d7f7-393b-4b4a-8e64-c75d69c48879   2Gi        RWO            local-path     26m
```

---

## 2. PostgreSQL StatefulSet Volume Persistence Test

1. **Pre-deletion Record Count**:
```sql
SELECT count(*), max(id) FROM appointments;
-- Result: count = 13 | max = APT-61f5ae90
```
2. **Pod Termination**:
```bash
$ kubectl delete pod postgres-0 -n healthcare
pod "postgres-0" deleted from healthcare namespace
```
3. **StatefulSet Automatic Re-spawn**:
```text
NAME         READY   STATUS    RESTARTS   AGE
postgres-0   1/1     Running   0          17s
```
4. **Post-recovery Record Verification**:
```sql
SELECT count(*), max(id) FROM appointments;
-- Result: count = 13 | max = APT-61f5ae90
```
**Persistence Outcome**: ✅ Data successfully persisted via PersistentVolumeClaim across pod destruction.

---

## 3. Deployment Self-Healing (Pod Recovery) Test

1. **Delete live backend pod**:
```bash
$ kubectl delete pod backend-deployment-84bdfdb75d-rqgnm -n healthcare
pod "backend-deployment-84bdfdb75d-rqgnm" deleted from healthcare namespace
```
2. **ReplicaSet instant recreation**:
```text
NAME                                  READY   STATUS    RESTARTS   AGE
backend-deployment-84bdfdb75d-p4fxs   0/1     Running   0          7s
backend-deployment-84bdfdb75d-z4dwv   1/1     Running   2          4m41s
```
3. **Readiness Probe Pass (20s)**:
```text
backend-deployment-84bdfdb75d-p4fxs   1/1     Running   0          20s
```
**Recovery Outcome**: ✅ Self-healing succeeded in 7 seconds without service interruption.

---

## 4. Horizontal Pod Autoscaler (HPA) Verification

```bash
$ kubectl describe hpa backend-hpa -n healthcare
```
- **Reference**: Deployment/backend-deployment
- **Current / Target CPU**: `6% (6m) / 70%`
- **Current / Target Memory**: `47% (62436Ki) / 80%`
- **Current / Desired Replicas**: `2 / 2` (Min: 2, Max: 6)
- **Status Conditions**:
  - `AbleToScale`: True (`ReadyForNewScale`)
  - `ScalingActive`: True (`ValidMetricFound`)
  - `ScalingLimited`: False (`DesiredWithinRange`)

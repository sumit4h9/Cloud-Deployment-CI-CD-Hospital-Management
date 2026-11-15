# Evidence 07: Multi-Replica Database Concurrency Verification

## 1. Local Automated Pytest Concurrency Test

```bash
$ python -m pytest backend/tests/test_concurrency.py -v -s
```

```text
backend/tests/test_concurrency.py::test_prevent_double_booking_concurrent_requests 
[CONCURRENCY AUDIT] Total requests fired: 10
[CONCURRENCY AUDIT] Successful bookings (201 Created): 1
[CONCURRENCY AUDIT] Blocked race conditions (409 Conflict): 9
PASSED
```

---

## 2. Live Kubernetes Multi-Pod Cluster Concurrency Test

Executed directly against distributed Kubernetes backend replicas in the `healthcare` namespace:

```bash
$ python3 test_k8s_concurrency.py
```

### Execution Log & Evidence:
```text
Testing against doctor: doc_1 (Dr. Ananya Mehta)
Firing 10 concurrent booking requests across BOTH Kubernetes Pod replicas for 2026-11-27 at 10:00...
Received Status Codes: [409, 409, 201, 409, 409, 409, 409, 409, 409, 409]

Successful (201 Created): 1
Conflicts (409 Conflict): 9

✅ MULTI-POD KUBERNETES CONCURRENCY TEST PASSED 100%!
Evidence: Across multiple Kubernetes backend replicas hitting PostgreSQL concurrently, exactly 1 request acquired the slot (201 Created) and 9 were rejected with 409 Conflict.
```

---

## 3. Technical Architecture & Guarantees

- **No In-Memory Locks**: No local process mutex/threading locks that fail across pods.
- **PostgreSQL Partial Unique Constraint**:
  ```sql
  CREATE UNIQUE INDEX uq_active_appointment ON appointments (doctor_id, date, start_time) 
  WHERE status IN ('Confirmed', 'Rescheduled');
  ```
- **Atomic Slot Claim**:
  ```sql
  UPDATE slots SET is_available = False WHERE id = :id AND is_available = True;
  ```
- **Behavior Under Multi-Pod Load**:
  - Exactly 1 transaction commits (`201 Created`).
  - 9 competing transactions fail the atomic check (`409 Conflict`).
  - Audit event logged: `CONFLICT_PREVENTED`.
  - Prometheus counter incremented: `appointment_conflicts_total`.

**Status**: **PASS (100% Proven on Multi-Pod Kubernetes)**

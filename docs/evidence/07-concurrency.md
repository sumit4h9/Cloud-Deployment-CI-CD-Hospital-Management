# Evidence 07: Multi-Replica Database Concurrency Verification

```bash
$ python -m pytest backend/tests/test_concurrency.py -v -s
```

### Execution Output:
```text
backend/tests/test_concurrency.py::test_prevent_double_booking_concurrent_requests 
[CONCURRENCY AUDIT] Total requests fired: 10
[CONCURRENCY AUDIT] Successful bookings (201 Created): 1
[CONCURRENCY AUDIT] Blocked race conditions (409 Conflict): 9
PASSED
```

### Technical Guarantee:
- Elimination of in-memory `threading.Lock` across distributed pods.
- Enforced by PostgreSQL / SQLite partial unique index:
  `CREATE UNIQUE INDEX uq_active_appointment ON appointments (doctor_id, date, start_time) WHERE status IN ('Confirmed', 'Rescheduled');`
- Enforced by atomic conditional slot reservation:
  `UPDATE slots SET is_available = False WHERE id = :id AND is_available = True`
- Exactly 1 request acquires the slot and commits.
- Remaining 9 concurrent requests fail database constraint, record `CONFLICT_PREVENTED` in the audit stream, increment Prometheus counter, and return `HTTP 409 Conflict`.

Status: **PASS**


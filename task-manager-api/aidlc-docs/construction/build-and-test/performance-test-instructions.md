# Performance Test Instructions — Task Manager API

## Scope Assessment

**Status**: Baseline performance validation only — full load/stress testing is **N/A for local dev PoC scope**.

Per NFR requirements (local development, small scale, single-user JSON storage), the following apply:

| Test Type | Status | Reason |
|---|---|---|
| Response time baseline | ✅ Applicable | Verify no obvious regressions |
| Load testing | N/A | JSON flat-file storage is not designed for concurrent writes |
| Stress testing | N/A | Single uvicorn worker, local dev only |
| Scalability testing | N/A | No scaling planned for this scope |

> **Note**: Before moving to production, replace JSON file storage with a proper database and run full performance testing.

---

## Baseline Response Time Verification

### Using httpx (Python)

```python
# Save as scripts/perf_baseline.py and run: python scripts/perf_baseline.py
import httpx
import time

BASE = "http://127.0.0.1:8000"

# 1. Login
resp = httpx.post(f"{BASE}/auth/login", json={"email": "test@example.com", "password": "Password1"})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Measure list tasks (cold)
start = time.perf_counter()
resp = httpx.get(f"{BASE}/tasks/", headers=headers)
elapsed = (time.perf_counter() - start) * 1000
print(f"GET /tasks/ (cold): {elapsed:.1f}ms — status {resp.status_code}")

# 3. Measure 10 sequential list calls
times = []
for _ in range(10):
    start = time.perf_counter()
    httpx.get(f"{BASE}/tasks/", headers=headers)
    times.append((time.perf_counter() - start) * 1000)
print(f"GET /tasks/ p50: {sorted(times)[5]:.1f}ms, p95: {sorted(times)[9]:.1f}ms")
```

### Expected Baselines (local dev, small dataset)

| Endpoint | Expected p50 | Expected p95 |
|---|---|---|
| `GET /health/live` | < 5ms | < 10ms |
| `GET /tasks/` (empty) | < 20ms | < 50ms |
| `POST /tasks/` | < 30ms | < 60ms |
| `GET /tasks/{id}` | < 20ms | < 50ms |

> These are guidance targets only — bcrypt hashing on login will take ~200–400ms by design (cost-12).

---

## Rate Limit Verification

Verify slowapi is correctly rejecting excess requests:

```bash
# Send 101 requests rapidly — the 101st should return 429
for i in $(seq 1 101); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer <token>" \
    http://localhost:8000/tasks/
done | sort | uniq -c
# Expected: 100× "200", 1× "429"
```

---

## Future Performance Work (Pre-Production)

When moving beyond local dev:

1. **Replace JSON storage** with PostgreSQL or DynamoDB
2. **Add connection pooling** (SQLAlchemy async or aiobotocore)
3. **Switch to multiple uvicorn workers** or gunicorn
4. **Run load test** with [k6](https://k6.io) or [Locust](https://locust.io):
   ```bash
   pip install locust
   locust -f tests/perf/locustfile.py --headless -u 50 -r 5 --run-time 60s
   ```
5. **Target SLAs**: p99 < 200ms for reads, p99 < 500ms for writes

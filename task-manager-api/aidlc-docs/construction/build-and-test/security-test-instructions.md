# Security Test Instructions — Task Manager API

> Required by Security Baseline extension (enabled). Covers manual verification of all SECURITY-* rules.

---

## SECURITY-01: No Hardcoded Secrets

```bash
# Search for hardcoded tokens/passwords in source
python -m grep -rn "password\s*=" src/ --include="*.py"
python -m grep -rn "secret\s*=" src/ --include="*.py"
python -m grep -rn "JWT_SECRET" src/ --include="*.py"
```
**Expected**: All secrets come from `settings` (pydantic-settings), not hardcoded.

---

## SECURITY-03: Structured Logging (No Sensitive Data in Logs)

Start the server and make a login request. Verify logs:
```bash
python -m uvicorn src.main:app --reload 2>&1 | grep -i "password\|hash\|token"
```
**Expected**: No password hashes, tokens, or credentials in logs. Only `request_start`, `request_complete`, `task_created`, etc.

---

## SECURITY-05: Input Validation

```bash
# Test SQL injection (should return 422)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"a@b.com\" OR 1=1--","password":"Password1"}'

# Test oversized title (should return 422)
curl -X POST http://localhost:8000/tasks/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"$(python -c 'print("x"*300)')\"}"

# Test oversized tag (should return 422)
curl -X POST http://localhost:8000/tasks/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"T\",\"tags\":[\"$(python -c 'print("x"*51)')\"]}"
```
**Expected**: All return 422 Unprocessable Entity.

---

## SECURITY-06: JWT Validation

```bash
# Tampered token (should return 401)
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.tampered.signature"

# Expired token — set JWT_EXPIRY_MINUTES=0 in .env, login, wait 1 min, then:
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <expired_token>"
```
**Expected**: Both return 401.

---

## SECURITY-07: Password Hashing

```bash
# Check that users.json never contains plaintext passwords
cat data/users.json | python -m json.tool | grep -i password
```
**Expected**: Only `password_hash` field with `$2b$12$...` bcrypt hash, no plaintext.

---

## SECURITY-08: Object-Level Authorization

```bash
# Register two users: alice and bob
# Login as alice, create a task → task_id
# Login as bob, attempt to update alice's task (should return 403)
curl -X PUT http://localhost:8000/tasks/<task_id> \
  -H "Authorization: Bearer <bob_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Hijacked"}'

# Bob attempt to delete alice's task (should return 403)
curl -X DELETE http://localhost:8000/tasks/<task_id> \
  -H "Authorization: Bearer <bob_token>"
```
**Expected**: Both return 403 Forbidden.

---

## SECURITY-09: Generic Error Messages

```bash
# Login with wrong password
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"WrongPassword"}'
```
**Expected**: Generic error message — NOT "wrong password" or "user not found" (prevents user enumeration).

---

## SECURITY-10: Account Lockout (BR-AUTH-02 + SECURITY-12 partial)

```bash
# Attempt login 5 times with wrong password
for i in 1 2 3 4 5; do
  curl -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"alice@example.com","password":"wrong"}'
done

# 6th attempt — even with correct password — should return 423 or lockout message
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Password1"}'
```
**Expected**: Account locked out for 15 minutes after 5 failed attempts.

---

## SECURITY-11: Rate Limiting

```bash
# Send 101 requests to a protected endpoint in rapid succession
python -c "
import httpx, time
token = '<your_token>'
headers = {'Authorization': f'Bearer {token}'}
statuses = []
for i in range(101):
    r = httpx.get('http://localhost:8000/tasks/', headers=headers)
    statuses.append(r.status_code)
from collections import Counter
print(Counter(statuses))
"
```
**Expected**: ~100 `200` responses, then `429` responses.

---

## SECURITY-12: Known Gap — Breached Password Check

**Status**: NON-COMPLIANT (accepted risk for local dev PoC)

This check was explicitly skipped (user decision Q2=C during requirements). The minimum 8-character requirement IS enforced. Breached password API integration must be added before production deployment.

**Verification** (confirm gap is documented):
```bash
# This should succeed even if "Password1" is a common password
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Password1"}'
```
**Expected**: 201 Created (breached check not performed — known gap).

---

## Dependency Security Scan

```bash
pip install pip-audit
pip-audit -r requirements.txt
```
**Expected**: No known vulnerabilities in dependencies. Address any HIGH/CRITICAL findings before production.

---

## CORS Verification

```bash
curl -X OPTIONS http://localhost:8000/tasks/ \
  -H "Origin: http://evil.com" \
  -H "Access-Control-Request-Method: DELETE" -v 2>&1 | grep -i "access-control"
```
**Expected**: `Access-Control-Allow-Origin: *` — permissive for local dev. **Must be tightened before production.**

---

## Security Test Summary Matrix

| Rule | Test Method | Expected Result |
|---|---|---|
| SECURITY-01 (No hardcoded secrets) | grep source | No hardcoded values |
| SECURITY-03 (Structured logging) | Inspect logs | No sensitive data in logs |
| SECURITY-05 (Input validation) | Send malformed input | 422 responses |
| SECURITY-06 (JWT validation) | Tampered/expired token | 401 responses |
| SECURITY-07 (Password hashing) | Inspect users.json | bcrypt hashes only |
| SECURITY-08 (Object-level auth) | Cross-user access | 403 responses |
| SECURITY-09 (Generic errors) | Wrong credentials | Generic messages |
| SECURITY-10 (Account lockout) | 5 failed logins | Account locked 15 min |
| SECURITY-11 (Rate limiting) | 101 requests | 429 after limit |
| SECURITY-12 (Breached passwords) | N/A (known gap) | Gap documented |

# Business Logic Model — Unit 1: Authentication

## Workflow 1: Register User

```
Input: UserCreate { email, password, full_name? }

1. Normalize email → lowercase
2. Validate email format (RFC 5322) → 422 if invalid
3. Validate password length >= 8 chars → 422 if too short
4. Look up user by normalized email
   → If found: raise ConflictError (409) with generic message
5. Hash password with bcrypt (cost factor 12)
6. Create User entity:
   id              = uuid4()
   email           = normalized_email
   password_hash   = bcrypt_hash
   full_name       = full_name or None
   failed_login_attempts = 0
   lockout_until   = None
   created_at      = utcnow()
   updated_at      = utcnow()
7. Persist user to users.json
8. Return UserResponse (id, email, full_name, created_at) — NO password_hash
```

---

## Workflow 2: Login

```
Input: LoginRequest { email, password }

1. Normalize email → lowercase
2. Look up user by normalized email
   → user_found = True/False (evaluate together in step 3 to prevent timing attacks)
3. IF user not found OR account locked (lockout_until > utcnow()):
   → If locked: raise UnauthorizedError (401) — "Account is temporarily locked"
   → If not found: raise UnauthorizedError (401) — "Invalid credentials"
   (Both cases use constant-time path to prevent timing-based user enumeration)
4. Verify password against password_hash (bcrypt constant-time)
   → If wrong:
      a. Increment user.failed_login_attempts += 1
      b. If failed_login_attempts >= 5:
            set user.lockout_until = utcnow() + timedelta(minutes=15)
      c. Persist updated user
      d. Raise UnauthorizedError (401) — "Invalid credentials"
   → If correct:
      a. Reset user.failed_login_attempts = 0
      b. Set user.lockout_until = None
      c. Persist updated user
5. Create JWT:
   payload = {
     "sub": str(user.id),
     "email": user.email,
     "iat": utcnow(),
     "exp": utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES)
   }
   token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
6. Return TokenResponse { access_token, token_type="bearer", expires_in }
```

---

## Workflow 3: Logout

```
Input: Authorization: Bearer <token>

1. Extract token from Authorization header → 401 if missing/malformed
2. Decode JWT (validate signature + expiry) → 401 if invalid/expired
3. Check token not in blacklist → 401 if already blacklisted
4. Add token string to blacklist set (idempotent — no-op if already present)
5. Return 200 OK
```

---

## Workflow 4: Token Validation (get_current_user dependency)

```
Input: Authorization: Bearer <token> (from request header)

1. Extract Bearer token → 401 if header missing or not "Bearer <token>"
2. Decode JWT:
   a. Verify signature (JWT_SECRET_KEY, HS256) → 401 if invalid
   b. Check exp claim > utcnow() → 401 if expired
3. Check token not in blacklist → 401 if blacklisted
4. Extract user_id = payload["sub"]
5. Look up user by user_id → 401 if user no longer exists
6. Return UserResponse (for injection into route handler)

Note: This workflow runs on EVERY protected request — must be fast.
All failures return HTTP 401 with the same generic message regardless of failure cause.
```

---

## Testable Properties (PBT-01 Identification)

### Property 1: Password Hash Round-Trip (PBT-02 — Round-trip)
```
For all valid plaintext passwords p:
  verify_password(p, hash_password(p)) == True

For all valid plaintext passwords p and wrong passwords w (p != w):
  verify_password(w, hash_password(p)) == False
```
**Category**: Round-trip (hash is the forward transform; verify is the inverse check)
**Generator**: Strings with length 8–128, printable ASCII

---

### Property 2: JWT Create/Decode Round-Trip (PBT-02 — Round-trip)
```
For all valid payloads d (dict with str keys, JSON-serialisable values):
  decode_access_token(create_access_token(d, expiry)) contains all keys/values from d
  (expiry is a positive integer)
```
**Category**: Round-trip
**Generator**: Dicts with user UUID strings and email strings

---

### Property 3: Token Blacklist Idempotency (PBT-04 — Idempotence)
```
For all valid token strings t:
  state_after_one_blacklist(t) == state_after_two_blacklists(t)
  (is_token_blacklisted(t) == True after 1 or 2 calls to blacklist_token(t))
```
**Category**: Idempotence

---

### Property 4: Failed Login Counter Invariant (PBT-03 — Invariant)
```
For any sequence of failed login attempts on the same user:
  user.failed_login_attempts >= 0 (never negative)
  After a successful login: user.failed_login_attempts == 0
```
**Category**: Invariant

---

### Property 5: Account Lockout Invariant (PBT-03 — Invariant)
```
For any user u with failed_login_attempts < 5:
  u.lockout_until is None

For any user u where the 5th consecutive failure just occurred:
  u.lockout_until > utcnow()
  u.lockout_until <= utcnow() + timedelta(minutes=15) + epsilon
```
**Category**: Invariant

---

### Property 6: Email Normalization Invariant (PBT-03 — Invariant)
```
For all email strings e registered or looked up:
  stored_email == e.lower()
  lookup(e.upper()) finds the same user as lookup(e.lower())
```
**Category**: Invariant

---

## Error Scenarios

| Scenario | Workflow | Rule | HTTP Response |
|---|---|---|---|
| Invalid email format | Register | BR-AUTH-01.1 | 422 — field validation error |
| Duplicate email | Register | BR-AUTH-01.3 | 409 — generic conflict message |
| Password < 8 chars | Register | BR-AUTH-01.4 | 422 — field validation error |
| Account locked | Login | BR-AUTH-02.2 | 401 — "Account is temporarily locked" |
| Wrong password (< 5 attempts) | Login | BR-AUTH-02.5 | 401 — "Invalid credentials" |
| Wrong password (5th attempt) | Login | BR-AUTH-02.6 | 401 — "Invalid credentials" (lock applied) |
| User not found | Login | BR-AUTH-02.3 | 401 — "Invalid credentials" (identical to wrong password) |
| Missing Authorization header | Token validation | BR-AUTH-03.1 | 401 — "Not authenticated" |
| Invalid JWT signature | Token validation | BR-AUTH-03.2 | 401 — "Invalid token" |
| Expired JWT | Token validation | BR-AUTH-03.3 | 401 — "Token expired" |
| Blacklisted token | Token validation | BR-AUTH-03.4 | 401 — "Invalid token" |
| User deleted after token issued | Token validation | BR-AUTH-03.5 | 401 — "Invalid token" |
| Invalid token at logout | Logout | BR-AUTH-04.1 | 401 — "Invalid token" |

# Domain Entities — Unit 1: Authentication

## Entity: User

**Description**: Represents a registered application user. The central identity entity — all other domain objects reference Users by ID.

### Fields

| Field | Type | Constraints | Default |
|---|---|---|---|
| `id` | UUID | System-generated, immutable, unique | `uuid4()` on creation |
| `email` | str | Required, unique (case-insensitive), max 254 chars, valid email format, stored lowercase | — |
| `password_hash` | str | Required, bcrypt hash, never plain-text, never returned in responses | — |
| `full_name` | str \| None | Optional, max 100 chars | `None` |
| `failed_login_attempts` | int | Non-negative integer, reset to 0 on successful login | `0` |
| `lockout_until` | datetime \| None | UTC datetime; `None` = not locked; set to `now + 15min` when threshold reached | `None` |
| `created_at` | datetime | UTC, immutable, set on creation | `utcnow()` on creation |
| `updated_at` | datetime | UTC, updated on every write | `utcnow()` on each write |

### Business Invariants
- `email` is always stored in lowercase (normalized before persist and lookup)
- `password_hash` is never `None` or empty after registration
- `failed_login_attempts` is always >= 0
- `lockout_until` is always `None` or a future-or-past UTC datetime (past = expired lock)
- `id` never changes after creation

### Persistence
- Stored as JSON objects in `data/users.json`
- `password_hash` field is present on disk but **never** included in any API response
- `failed_login_attempts` and `lockout_until` are internal state, not exposed in API responses

---

## Entity: TokenBlacklist

**Description**: Tracks invalidated JWT tokens (logged-out sessions). Prevents reuse of valid-signature tokens after logout.

### Structure
- **Type**: In-memory `set[str]` — set of raw JWT token strings
- **Lifetime**: Process lifetime only — cleared on application restart (known local-dev constraint)
- **Backed by**: `core/security.py` module-level set

### Fields

| Field | Type | Notes |
|---|---|---|
| `token` | str | Raw JWT string (full token, not just the payload) |

### Business Invariants
- Adding a token already in the blacklist is a no-op (idempotent)
- Membership check is O(1) via set hash lookup
- The set is append-only — tokens are never removed from the blacklist (they expire naturally via JWT expiry)

### Limitations (documented)
- Not persisted — tokens removed from blacklist on application restart
- Acceptable for local development; production would use a persistent store (Redis, DB table)

---

## Value Objects

### Email
- **Type**: `str`
- **Validation**: RFC 5322 format, max 254 chars
- **Normalization**: Always stored and compared as lowercase
- **Used by**: User entity (registration, login lookup)

### PasswordPlaintext
- **Type**: `str`
- **Validation**: Minimum 8 characters
- **Note**: Exists only transiently — never stored; passed to bcrypt and discarded
- **Breached password check**: Skipped (known gap — see business-rules.md SECURITY-12 note)

### PasswordHash
- **Type**: `str`
- **Algorithm**: bcrypt with cost factor 12
- **Used by**: User entity (stored as `password_hash`), SecurityUtils (verify)

### JWTToken
- **Type**: `str`
- **Structure**: Standard JWT — header.payload.signature
- **Algorithm**: HS256
- **Payload claims**: `sub` (user UUID), `email`, `exp` (expiry), `iat` (issued at)
- **Expiry**: Configurable via `JWT_EXPIRY_MINUTES` setting (default: 60 minutes)

### LoginFailureRecord (logical, embedded in User)
- **Fields**: `failed_login_attempts: int`, `lockout_until: datetime | None`
- **Lockout threshold**: 5 consecutive failures
- **Lockout duration**: 15 minutes from the moment of the 5th failure
- **Reset condition**: Successful login resets both fields to their defaults

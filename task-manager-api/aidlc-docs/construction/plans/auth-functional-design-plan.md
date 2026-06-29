# Functional Design Plan — Unit 1: Authentication

Please answer the 2 questions below. All other functional design decisions are clear from the
requirements, stories, and security rules. Let me know when done.

---

## Question 1: Brute-Force Protection on Login (SECURITY-12)

SECURITY-12 requires the login endpoint to implement account lockout, progressive delays, or
CAPTCHA after repeated failures. Which approach should be used?

A) Progressive delay — each successive failed login attempt for the same email adds an
   increasing delay before the response is returned (e.g., 0s, 1s, 2s, 4s, ...).
   Simple to implement, no persistent state needed.

B) Account lockout — after N consecutive failures (e.g., 5), the account is temporarily
   locked for a fixed period (e.g., 15 minutes). Requires tracking failure counts
   per user in the data store.

C) No brute-force protection — document as a known accepted risk with explicit justification
   (only acceptable if Security extension is downgraded to non-blocking for this rule).

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 2: Breached Password Check (SECURITY-12)

SECURITY-12 requires passwords to be checked against breached password lists. Which approach
should be used for this local development project?

A) Local blocklist — maintain a small hardcoded list of the most common weak passwords
   (e.g., top-100 common passwords). Rejects any password on the list. No external API
   calls, no internet required, zero complexity.

B) Have I Been Pwned (HIBP) k-anonymity API — hash the password, send the first 5 chars
   of the SHA-1 hash to `api.pwnedpasswords.com`. Full breach coverage but requires
   outbound internet access during registration.

C) Skip breached password check — document as a known gap with explicit SECURITY-12
   non-compliance justification (local dev PoC scope). Minimum 8-char requirement still enforced.

X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Artifacts to Generate (After Questions Answered)

- [x] `aidlc-docs/construction/auth/functional-design/domain-entities.md`
  - [x] User entity with all fields, types, constraints
  - [x] TokenBlacklist entity
  - [x] Value objects: Email, PasswordHash, JWTToken
- [x] `aidlc-docs/construction/auth/functional-design/business-rules.md`
  - [x] Registration rules (email uniqueness, password policy, hashing)
  - [x] Login rules (credential verification, token issuance, brute-force protection)
  - [x] Logout rules (token validation, blacklisting)
  - [x] Token validation rules (signature, expiry, blacklist check)
- [x] `aidlc-docs/construction/auth/functional-design/business-logic-model.md`
  - [x] Auth workflows (register, login, logout, validate)
  - [x] Testable properties (PBT-01 identification)
  - [x] Error scenarios per workflow

# DPS AI Interview System Backend V11

V11 is the Security Acceptance and Authorization Hardening release.

## Main changes

1. Centralized interview authorization.
2. Reviewer queue visibility enforced consistently.
3. Reviewer write access removed from transcript and form evidence.
4. Recording download authorization hardened.
5. Interviewer candidate isolation tightened.
6. Refresh-token rotation protected with row locking.
7. Last active administrator protection added.
8. Application version advanced to 0.11.0.

## Validation

35 unit and security tests passed.

Integration tests requiring aiosqlite remain blocked in the current execution environment. PostgreSQL-backed concurrency tests require a real PostgreSQL environment and have not been claimed as passed.

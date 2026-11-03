# Threat Model

Assets: student and parent audio, transcripts, forms, staff identities, review decisions, audit records.

Primary threats: broken access control, unauthorized recording downloads, malicious uploads, prompt injection through transcript content, model hallucination, credential attacks, excessive AI job submission, log leakage, backup exposure, and privileged account misuse.

Current mitigations: backend RBAC dependencies, non-sequential UUID identifiers, private storage abstraction, upload MIME and size validation, SHA-256 checksums, Argon2 password hashing, short-lived access tokens, server-tracked refresh sessions, login failure lockout, security headers, correlation IDs, no transcript logging, structured AI validation, human review before finalization, and explicit workflow transitions.

Remaining hardening: production rate limiting, secure cookie session mode if selected by the frontend architecture, CSRF strategy for cookie authentication, malware/content scanning for uploaded files, object-storage signed access, centralized audit protection, backup encryption, dependency/container scanning, formal penetration testing, and school/legal privacy approval.

## V11 authorization acceptance additions

The V11 security pass specifically addresses OWASP API risks around broken object-level authorization, broken function-level authorization, and broken object-property access. Resource access now uses a centralized interview authorization boundary rather than repeating partial ownership checks in individual endpoints. Reviewers are restricted to the review lifecycle and cannot mutate interview evidence. The refresh-session lookup uses a database row lock during refresh rotation to reduce concurrent token reuse races. The application also prevents removal of the last active administrator.

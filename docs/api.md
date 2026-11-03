# API Overview

Base path: `/api/v1`

## Authentication
- POST `/auth/login`
- POST `/auth/refresh`
- POST `/auth/logout`
- POST `/auth/password-reset/request`
- POST `/auth/password-reset/confirm`
- GET `/auth/me`
- POST `/auth/users` (administrator)

## Users
- GET `/users` (administrator)
- PATCH `/users/{user_id}` (administrator)

## Candidates
- POST `/candidates`
- GET `/candidates`
- GET `/candidates/{candidate_id}`
- PATCH `/candidates/{candidate_id}`

## Interviews
- POST `/interviews`
- GET `/interviews`
- GET `/interviews/{interview_id}`
- POST `/interviews/{interview_id}/consent`
- POST `/interviews/{interview_id}/recording-start`
- POST `/interviews/{interview_id}/submit`

## Recordings and processing
- POST `/recordings/{interview_id}` multipart upload
- GET `/recordings/{interview_id}/download`
- GET `/processing/{interview_id}`
- POST `/processing/run-once` (administrator)

## AI output
- GET `/transcriptions/{interview_id}`
- PATCH `/transcriptions/segments/{segment_id}`
- GET `/summaries/{interview_id}`

## Forms and review
- GET `/forms/{interview_id}`
- PATCH `/forms/{form_id}/fields/{field_id}`
- GET `/forms/{interview_id}/pdf`
- POST `/reviews/{interview_id}`

## Templates and administration
- GET `/templates`
- POST `/templates` (administrator)
- GET `/templates/{template_id}/versions`
- GET `/admin/jobs` (administrator)
- GET `/admin/audit` (administrator)
- GET `/health/live`
- GET `/health/ready`

FastAPI generates the interactive OpenAPI documentation at `/docs` when the application is running.

## Review lifecycle

Reviewer actions use `POST /api/v1/reviews/{interview_id}`.

- `review` from `submitted` moves the interview to `principal_review`.
- `review` from `principal_review` moves the interview to `reviewed`, but only when every form field has left `needs_review`.
- `request_correction` is allowed only in `principal_review` and requires correction remarks. The interview moves to `correction_requested`.
- `finalize` is allowed only in `reviewed` and moves the interview to `finalized`.

The interviewer submission endpoint now leaves the interview in `submitted`; principal review is an explicit reviewer step.

## V9 Collection Contract

Collection endpoints that support pagination return:

```json
{
  "items": [],
  "meta": {
    "total": 0,
    "skip": 0,
    "limit": 50,
    "has_more": false
  }
}
```

Candidate listing: `GET /api/v1/candidates?skip=0&limit=50&q=...`

Interview listing: `GET /api/v1/interviews?skip=0&limit=50&status=submitted`

Admin jobs: `GET /api/v1/admin/jobs?skip=0&limit=50&status=queued`

Admin audit: `GET /api/v1/admin/audit?skip=0&limit=50&action=...`

Users: `GET /api/v1/users?skip=0&limit=50&role=interviewer`

Limits are server bounded to prevent unbounded collection responses. The frontend should use the returned `meta` object instead of inferring pagination from item counts.

## Authorization boundaries

Interview resources use a centralized authorization policy. Interviewers may access only their assigned interviews. Reviewers may access only interviews in submitted, principal review, correction requested, reviewed, or finalized states. Reviewers are read-only for transcript and form evidence. Reviewed and finalized interviews cannot be modified through transcript or form editing endpoints. Recording downloads apply the same reviewer visibility boundary.

Candidate listing and retrieval for interviewers is limited to candidates currently assigned to that interviewer.

## Frontend integration metadata

`GET /api/v1/meta` returns non-secret application metadata for the frontend, including supported roles, interview lifecycle statuses, feature availability, and upload constraints. It must not be used as an authorization source; server-side RBAC remains authoritative.

## V18 Demo Deployment

The repository includes `docker-compose.demo.yml` for a PostgreSQL + migration + backend + worker demo stack. The migration service runs before the API and worker. The backend then seeds the initial administrator and demo interview template without enabling automatic schema creation. See `docs/v18-demo-deployment.md`.

# V16 Release Notes

## API Contract and Demo Integration Readiness

V16 is the backend contract hardening phase before frontend integration.

### Changes

- Added `GET /api/v1/meta` for non-secret frontend integration metadata.
- Added a typed `UserPage` response model so the users endpoint matches its paginated response.
- Candidate PATCH now respects explicit nullable fields by using Pydantic `exclude_unset` semantics.
- API root now reports version `0.16.0` and the versioned API prefix.
- Removed an accidental temporary interview source artifact.
- Added `scripts/export_openapi.py` for generating the frontend-facing OpenAPI contract.
- Documented the V16 release boundary.

### Security boundary

The metadata endpoint does not expose API keys, database URLs, storage paths, JWT secrets, or provider credentials.

### Frontend contract

Run from `backend/`:

```bash
python ../scripts/export_openapi.py
```

This generates `docs/openapi.json` from the running FastAPI application definition. Generate it in the same environment used for frontend integration so the contract reflects the installed backend dependencies and routes.

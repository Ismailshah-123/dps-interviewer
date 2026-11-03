# DPS V18 Frontend and Backend Integration

The repository now contains the V18 backend and the V16 frontend implementation in one demo package.

## Local browser test

1. Start PostgreSQL using the backend/demo Docker instructions.
2. Configure `backend/.env` with the database URL, secret, and Groq API key.
3. Run Alembic migrations.
4. Start FastAPI on `127.0.0.1:8000`.
5. Start the processing worker.
6. In `frontend`, copy `.env.example` to `.env.local`.
7. Run `npm install`.
8. Run `npm run dev`.
9. Open `http://localhost:3000`.

The frontend API base URL is `http://127.0.0.1:8000` by default and all application routes use `/api/v1`.

## Important

The frontend is a demo-ready integration layer, not production-certified. The official DPS form, approved consent/legal wording, real PostgreSQL staging run, live Groq run, accessibility audit, Playwright lifecycle run, and production dependency lockfile remain release gates.

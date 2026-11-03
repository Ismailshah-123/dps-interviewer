# DPS AI Student Interview System - Browser Demo

This package contains the V18 backend and the frontend together.

## 1. Backend

Open PowerShell in the repository root.

Configure `backend/.env` and set:

- PostgreSQL connection
- SECRET_KEY
- GROQ_API_KEY
- TRANSCRIPTION_PROVIDER=groq
- SUMMARIZATION_PROVIDER=groq
- GROQ_TRANSCRIPTION_MODEL=whisper-large-v3-turbo
- GROQ_SUMMARY_MODEL=openai/gpt-oss-20b

Start PostgreSQL, run migrations, then start FastAPI and the worker using the repository deployment documentation.

Backend should be available at:

`http://127.0.0.1:8000`

## 2. Frontend

Open a second PowerShell:

`cd frontend`

Copy `.env.example` to `.env.local`.

Then run:

`npm install`

`npm run dev`

Open:

`http://localhost:3000`

## 3. First test

Use a synthetic/consented demo student recording. Do not use real student data for the first test.

Test:

Login -> Candidate -> Interview -> Consent -> Upload Audio -> Processing -> Transcript -> AI Summary -> DPS Form -> Submit -> Review -> Finalize -> PDF

## 4. If anything fails

Capture the browser console, FastAPI terminal, and worker terminal output and send the exact error. Do not change random files before tracing the failure.

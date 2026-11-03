# Groq Demo Setup

## Purpose

Use Groq for the first DPS AI Interview System demonstration without placing an API key in the browser.

## Environment

Set these values in `backend/.env`:

```env
ENVIRONMENT=development
TRANSCRIPTION_PROVIDER=groq
SUMMARIZATION_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_TRANSCRIPTION_MODEL=whisper-large-v3-turbo
GROQ_SUMMARY_MODEL=openai/gpt-oss-20b
GROQ_MAX_AUDIO_BYTES=104857600
```

Keep `GROQ_API_KEY` server-side. Never commit `.env` or expose the key through frontend configuration.

## Start the backend

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

## Verify AI configuration

```text
GET /api/v1/health/ai
```

This endpoint does not call Groq. It only confirms that the providers can be constructed and reports the configured provider/model names.

## Demo workflow

1. Create/login as an interviewer.
2. Create a candidate.
3. Create an interview.
4. Confirm recording consent.
5. Upload a short interview recording.
6. Run/process the queued transcription job.
7. Review the timestamped transcript.
8. Run/process the summary job.
9. Review the AI-generated structured form draft.
10. Edit unclear or missing fields.
11. Submit for principal review.
12. Review or request correction.
13. Finalize after review.
14. Export the finalized PDF.

## Free-tier expectations

Groq account limits, model availability, rate limits, request-size limits and pricing/free-tier policies are external provider constraints. The application must treat 429 and transient 5xx responses as retryable and must not assume unlimited inference.

For a first demo, use short recordings and a small number of test interviews. Do not use real student data until the organization's privacy and data-processing requirements approve sending audio/transcript content to the configured external provider.

# V14 Release Notes

## Demo AI and Final Release Candidate Hardening

V14 prepares the backend for the first working DPS demonstration using a Groq API key and Groq hosted models while preserving provider abstraction for later production migration.

### Demo configuration

- Transcription provider: Groq
- Transcription model: whisper-large-v3-turbo
- Summary provider: Groq
- Default summary model: openai/gpt-oss-20b
- API key: server-side environment variable only

The demo model selection is intentionally conservative for free-tier experimentation. Model availability and provider rate limits are external infrastructure constraints and must be verified against the current Groq account before deployment.

### Provider reliability

Groq HTTP errors now expose a typed provider error. HTTP 408, 409, 425, 429 and 5xx responses are treated as retryable. If Groq returns a numeric Retry-After header, the worker respects it up to the platform's bounded retry window.

Authentication and other non-retryable errors are surfaced immediately and still enter the normal job failure/retry policy without blindly hammering the provider.

### AI health

`GET /api/v1/health/ai` performs a non-invasive configuration check. It does not call Groq and therefore does not consume inference quota.

It reports provider and configured model names without exposing API credentials.

### Privacy

Groq mode sends recorded audio for transcription and interview transcript content for summarization to the configured Groq endpoint. This must be explicitly approved by the deployment's privacy/data-processing policy before real student data is used.

### Release limitations

This release does not claim live Groq inference success, PostgreSQL runtime success, or provider quota availability in the development environment. Those require deployment credentials and infrastructure.

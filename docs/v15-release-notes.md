# V15 Release Notes

## Demo-ready AI backend completion pass

V15 closes the remaining demo-focused AI gaps while keeping the backend provider-agnostic.

### Groq demo configuration

The demo defaults to:

- Transcription: `whisper-large-v3-turbo`
- Summarization: `openai/gpt-oss-20b`
- Server-side `GROQ_API_KEY`
- Groq free-tier direct upload guard: 25 MiB

Groq's current documentation lists 25 MB as the direct-upload limit on the free tier and supports timestamped multilingual transcription with Whisper Large V3 Turbo. The backend therefore defaults to a 25 MiB guard for the free demo; a deployment can raise it when its account/tier permits a larger limit. See the current Groq documentation before changing the value.

### Structured AI output

GPT-OSS 20B now uses Groq Structured Outputs with strict JSON Schema. The summary schema includes transcript evidence references and unclear/missing information. The backend still validates the returned payload with Pydantic before it can enter the interview workflow.

### AI observability

Prometheus metrics now cover AI request counts, failures, and latency separately for transcription and summarization.

### Live demo smoke test

Use:

```bash
export GROQ_API_KEY="..."
python scripts/groq_demo_smoke.py ./path/to/consented-demo-audio.wav
```

The smoke test performs real Groq inference and therefore requires a real key and consented demo audio. It does not claim live provider success in CI or development environments where the key is absent.

### Privacy

Student audio and transcript content leave the local backend when Groq is enabled. Use only approved demo data until the deployment privacy/data-processing decision authorizes real student data.

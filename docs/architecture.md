# Architecture

```mermaid
flowchart LR
  Browser[React Browser] --> API[FastAPI API]
  API --> DB[(PostgreSQL)]
  API --> Store[(Private Audio/Object Storage)]
  API --> Jobs[(Processing Jobs)]
  Jobs --> Worker[AI Worker]
  Worker --> STT[Faster Whisper Adapter]
  Worker --> LLM[Ollama Adapter]
  Worker --> DB
  API --> PDF[PDF Generator]
  PDF --> Browser
```

## Trust boundaries

Browser is untrusted. Every record, file, export and workflow transition is authorized server-side.

Audio storage is private. Browser access is mediated through authenticated API endpoints.

Transcript content is untrusted input to the summarizer. It must never be treated as system instructions.

## Processing lifecycle

```mermaid
stateDiagram-v2
  [*] --> draft
  draft --> recording
  recording --> uploading
  uploading --> uploaded
  uploaded --> queued
  queued --> transcribing
  transcribing --> transcript_ready
  transcript_ready --> summarizing
  summarizing --> form_draft_ready
  form_draft_ready --> needs_review
  needs_review --> submitted
  submitted --> principal_review
  principal_review --> correction_requested
  principal_review --> reviewed
  correction_requested --> needs_review
  reviewed --> finalized
  transcribing --> failed
  summarizing --> failed
  failed --> queued
```

## Vertical slice today

The backend now contains the core domain model and APIs for the first end-to-end workflow. The frontend is intentionally not implemented in this backend pass.

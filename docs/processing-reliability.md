# Processing Reliability

The processing subsystem is intentionally designed around durable database jobs rather than an in-memory task list.

## Job lifecycle

`queued -> running -> completed`

Failures retry while `attempts < max_attempts`:

`running -> queued -> running ... -> failed`

Each retry receives a bounded exponential delay through `next_attempt_at`.

## Idempotency

Transcription jobs use:

`transcription:{interview_id}:{recording_sha256}`

Summary jobs use:

`summary:{interview_id}:{transcript_id}`

The database unique constraint prevents duplicate jobs for the same logical operation.

## Worker crash recovery

Running jobs carry `locked_at` and `heartbeat_at`. Jobs whose heartbeat is older than `PROCESSING_STALE_SECONDS` are recovered into the queue when retry attempts remain. Exhausted stale jobs are marked failed.

## Multi-worker claiming

PostgreSQL workers use row-level locking with `FOR UPDATE SKIP LOCKED` when claiming a queued job. This allows multiple workers to consume the same queue without intentionally processing the same row concurrently.

## Operational retry

Administrators can manually requeue failed or cancelled jobs through the admin retry endpoint after investigating the error.

## Remaining hardening

For high-volume deployment, add a dedicated queue/stream if database polling becomes a bottleneck, plus worker metrics, heartbeats during long model inference, distributed tracing and capacity-based autoscaling.

## Phase 7 hardening

The worker now maintains a separate heartbeat while a transcription or summarization provider call is in flight. This prevents a long-running AI request from being incorrectly recovered as stale when the provider call exceeds the normal heartbeat interval.

Administrators can cancel queued or running jobs through `POST /api/v1/processing/jobs/{job_id}/cancel`. An in-flight provider result is discarded after cancellation is detected, preventing a cancelled job from being marked completed.

The existing stale-job recovery remains active and uses the heartbeat timestamp. PostgreSQL row locking is still used when claiming jobs, so multiple workers can safely compete for the same queue.

## V10 retry recovery behavior

Administrative retry is a deliberate workflow recovery operation. When a failed transcription job is requeued, the worker restores the interview from `failed` to `queued` before entering `transcribing`. When a failed summary job is requeued, the worker restores the interview from `failed` to `transcript_ready` before entering `summarizing`. This prevents a previously failed interview state from blocking a legitimate retry.

An administrative retry resets the job attempt counter to zero and starts a fresh configured retry budget. The original failure remains visible through the processing and audit history.

Cancellation clears future scheduling so a cancelled job cannot be selected by a due-job query.

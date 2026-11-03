# V13 Operations Guide

## Health

- `GET /api/v1/health/live` confirms the process is alive.
- `GET /api/v1/health/ready` checks database and storage readiness.
- `GET /metrics` exposes Prometheus-compatible application metrics when enabled.

The metrics endpoint should be kept on an internal network or protected by the deployment gateway. Do not expose it directly to untrusted users.

## Metrics

The application records:

- HTTP request totals
- HTTP error totals
- HTTP latency
- Processing jobs completed
- Processing jobs failed
- Processing jobs retried
- Stale jobs recovered
- Currently running jobs

Metrics contain operational dimensions such as method, path, status, and job type. They do not contain transcript text, audio, passwords, JWTs, or provider payloads.

## Worker shutdown

The worker listens for SIGINT and SIGTERM. It stops accepting new polling iterations and exits after a short shutdown grace period. Jobs are persisted in PostgreSQL, so unfinished work can be recovered by the stale-job recovery mechanism after a worker process disappears.

## Database pool

Production PostgreSQL deployments can tune:

- `DB_POOL_SIZE`
- `DB_MAX_OVERFLOW`
- `DB_POOL_TIMEOUT_SECONDS`
- `DB_POOL_RECYCLE_SECONDS`

Start conservatively and size the pool against PostgreSQL connection limits and the number of API/worker processes.

## Telemetry roadmap

The base application uses Prometheus-compatible metrics and JSON logs without requiring a telemetry collector. OpenTelemetry may be layered on later for distributed traces and external metrics/log export. OpenTelemetry Python documents traces and metrics as stable and logs as development status at the time of V13. 

# V13 Release Notes

## Production reliability and observability

V13 adds operational telemetry and safer runtime configuration without making telemetry a source of truth for business state.

### Included

- JSON structured application logging
- Correlation ID propagation remains on every API response
- Prometheus metrics endpoint at `/metrics`
- HTTP request count, error count, and latency metrics
- Processing job completion, retry, failure, recovery, and running gauges
- PostgreSQL connection pool sizing and recycling configuration
- Configurable worker polling interval
- Graceful SIGINT/SIGTERM worker shutdown
- Worker iteration exception isolation so one unexpected loop error does not terminate the worker
- API version `0.13.0`

Metrics are disabled with `METRICS_ENABLED=false` when an environment does not expose a metrics endpoint.

## Security considerations

The metrics endpoint should not be exposed publicly without network or gateway controls. Telemetry must never include audio, transcript contents, passwords, access tokens, refresh tokens, or raw AI payloads.

OpenTelemetry can be added later as an external telemetry transport. The application remains usable without an observability collector. OpenTelemetry Python currently documents traces and metrics as stable and logs as development status, so this release keeps the base operational layer dependency-light. See the official documentation: https://opentelemetry.io/docs/languages/python/

## Validation

- Python compilation: required and executed
- Unit suite: run in the release environment
- PostgreSQL acceptance: remains environment-gated and must be executed against a real PostgreSQL instance
- No unavailable infrastructure is represented as passing

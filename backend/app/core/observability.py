import json
import logging
import time
from app.core.request_context import correlation_id
from contextvars import ContextVar
from typing import Any

from prometheus_client import Counter, Histogram, Gauge

request_started = Counter("dps_http_requests_total", "HTTP requests received", ["method", "path"])
request_failed = Counter("dps_http_failures_total", "HTTP requests returning errors", ["method", "path", "status"])
request_duration = Histogram("dps_http_request_duration_seconds", "HTTP request duration", ["method", "path"])
job_completed = Counter("dps_processing_jobs_completed_total", "Completed processing jobs", ["job_type"])
job_failed = Counter("dps_processing_jobs_failed_total", "Failed processing jobs", ["job_type"])
job_retried = Counter("dps_processing_jobs_retried_total", "Retried processing jobs", ["job_type"])
job_recovered = Counter("dps_processing_jobs_recovered_total", "Recovered stale jobs", ["job_type"])
job_running = Gauge("dps_processing_jobs_running", "Currently running processing jobs")
ai_requests = Counter("dps_ai_requests_total", "AI provider requests", ["provider", "operation", "model"])
ai_failures = Counter("dps_ai_failures_total", "AI provider failures", ["provider", "operation", "status"])
ai_duration = Histogram("dps_ai_request_duration_seconds", "AI provider request duration", ["provider", "operation"])

_sensitive = {"authorization", "cookie", "set-cookie", "password", "token", "access_token", "refresh_token"}


def configure_logging() -> None:
    if getattr(configure_logging, "_configured", False):
        return
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload: dict[str, Any] = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            for key in ("correlation_id", "event", "job_id", "job_type", "user_id", "path", "status_code"):
                value = correlation_id.get(None) if key == "correlation_id" else getattr(record, key, None)
                if value is not None:
                    payload[key] = value
            return json.dumps(payload, ensure_ascii=False)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    configure_logging._configured = True

from app.core.observability import request_started, request_failed, request_duration, job_completed, job_failed, job_retried, job_recovered, job_running


def test_observability_metrics_are_registered():
    assert request_started._name == "dps_http_requests"
    assert request_failed._name == "dps_http_failures"
    assert request_duration._name == "dps_http_request_duration_seconds"
    assert job_completed._name == "dps_processing_jobs_completed"
    assert job_failed._name == "dps_processing_jobs_failed"
    assert job_retried._name == "dps_processing_jobs_retried"
    assert job_recovered._name == "dps_processing_jobs_recovered"
    assert job_running._name == "dps_processing_jobs_running"

from app.services.processing_policy import should_retry, next_status

def test_retry_policy():
    assert should_retry(1, 3) is True
    assert next_status(1, 3) == "queued"
    assert should_retry(3, 3) is False
    assert next_status(3, 3) == "failed"

def should_retry(attempts: int, max_attempts: int) -> bool:
    return attempts < max_attempts

def next_status(attempts: int, max_attempts: int) -> str:
    return "queued" if should_retry(attempts, max_attempts) else "failed"

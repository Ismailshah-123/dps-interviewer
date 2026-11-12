import pytest

from app.api import recordings as recordings_api


async def test_cleanup_uncommitted_upload_deletes_object(monkeypatch):
    deleted = []

    async def fake_delete(key):
        deleted.append(key)

    monkeypatch.setattr(recordings_api.storage, "delete", fake_delete)

    await recordings_api._cleanup_uncommitted_upload("interviews/example/audio.webm")

    assert deleted == ["interviews/example/audio.webm"]


async def test_cleanup_failure_does_not_escape_or_mask_original_error(monkeypatch, caplog):
    async def failing_delete(key):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr(recordings_api.storage, "delete", failing_delete)

    # Cleanup is best-effort: its failure is logged for reconciliation,
    # but must not replace the original upload/database exception.
    await recordings_api._cleanup_uncommitted_upload("interviews/example/audio.webm")

    assert "Could not remove uncommitted recording object" in caplog.text

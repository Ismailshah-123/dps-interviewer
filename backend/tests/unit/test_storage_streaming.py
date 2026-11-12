from pathlib import Path

import pytest

from app.services.storage.local import LocalPrivateStorage
from app.services.storage.r2 import R2PrivateStorage


async def test_local_storage_streams_file_in_chunks(tmp_path):
    storage = LocalPrivateStorage(str(tmp_path))
    payload = b"0123456789" * 100
    path = storage.path_for("interviews/test/audio.webm")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)

    chunks = [chunk async for chunk in storage.stream("interviews/test/audio.webm", chunk_size=73)]

    assert b"".join(chunks) == payload
    assert len(chunks) > 1


class FakeBody:
    def __init__(self, payload):
        self.payload = payload
        self.closed = False

    def read(self, size):
        chunk, self.payload = self.payload[:size], self.payload[size:]
        return chunk

    def close(self):
        self.closed = True


class FakeR2Client:
    def __init__(self, body):
        self.body = body

    def get_object(self, **kwargs):
        return {"Body": self.body}


async def test_r2_storage_streams_and_closes_response_body():
    storage = object.__new__(R2PrivateStorage)
    body = FakeBody(b"cloudflare-r2-recording")
    storage.client = FakeR2Client(body)
    storage.bucket = "private-test-bucket"

    chunks = [chunk async for chunk in storage.stream("interviews/test/audio.webm", chunk_size=5)]

    assert b"".join(chunks) == b"cloudflare-r2-recording"
    assert body.closed is True


async def test_r2_storage_closes_body_when_consumer_stops_early():
    storage = object.__new__(R2PrivateStorage)
    body = FakeBody(b"large-recording-payload")
    storage.client = FakeR2Client(body)
    storage.bucket = "private-test-bucket"

    generator = storage.stream("interviews/test/audio.webm", chunk_size=5)
    first_chunk = await generator.__anext__()
    await generator.aclose()

    assert first_chunk == b"large"
    assert body.closed is True

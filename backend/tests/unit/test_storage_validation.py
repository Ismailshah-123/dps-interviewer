from pathlib import Path
from app.services.storage.local import LocalPrivateStorage

async def test_audio_signatures(tmp_path):
    storage = LocalPrivateStorage(str(tmp_path))
    wav = Path("wav")
    key = "x.wav"
    target = storage.path_for(key)
    target.write_bytes(b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 32)
    assert await storage.validate_audio_header(key, "audio/wav")

async def test_reject_mismatched_audio_signature(tmp_path):
    storage = LocalPrivateStorage(str(tmp_path))
    key = "x.webm"
    storage.path_for(key).write_bytes(b"RIFF" + b"\x00" * 40)
    assert not await storage.validate_audio_header(key, "audio/webm")

def test_storage_path_traversal_rejected(tmp_path):
    storage = LocalPrivateStorage(str(tmp_path))
    try:
        storage.path_for("../escape.wav")
        assert False, "path traversal must be rejected"
    except ValueError:
        pass

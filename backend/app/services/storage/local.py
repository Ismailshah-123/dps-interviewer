import hashlib
from pathlib import Path
from app.core.config import settings


AUDIO_SIGNATURES = {
    "audio/wav": lambda b: b[:4] == b"RIFF" and b[8:12] == b"WAVE",
    "audio/webm": lambda b: b[:4] == b"\x1a\x45\xdf\xa3",
    "audio/ogg": lambda b: b[:4] == b"OggS",
    "audio/mpeg": lambda b: b[:3] == b"ID3" or (len(b) >= 2 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0),
    "audio/mp4": lambda b: len(b) >= 12 and b[4:8] == b"ftyp",
    "audio/x-m4a": lambda b: len(b) >= 12 and b[4:8] == b"ftyp",
}


class LocalPrivateStorage:
    def __init__(self, root: str | None = None):
        self.root = Path(root or settings.storage_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def download_to_path(self, key: str, destination: Path):
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = self.path_for(key)
        import shutil
        shutil.copyfile(source, destination)

    def path_for(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root != path and self.root not in path.parents:
            raise ValueError("Invalid storage key")
        return path

    def validate_audio_header(self, key: str, mime_type: str) -> bool:
        path = self.path_for(key)
        with path.open("rb") as f:
            header = f.read(64)
        validator = AUDIO_SIGNATURES.get(mime_type)
        return bool(validator and validator(header))

    async def save_upload(self, upload, key: str, max_bytes: int):
        path = self.path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        total = 0
        digest = hashlib.sha256()
        with path.open("wb") as f:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    f.close()
                    path.unlink(missing_ok=True)
                    raise ValueError("File exceeds configured upload limit")
                digest.update(chunk)
                f.write(chunk)
        if total == 0:
            path.unlink(missing_ok=True)
            raise ValueError("Empty recording")
        return total, digest.hexdigest(), path

    async def save_bytes(self, key: str, data: bytes, content_type: str) -> None:
        path = self.path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        import asyncio
        await asyncio.to_thread(path.write_bytes, data)

    def open(self, key: str):
        return self.path_for(key).open("rb")

    def delete(self, key: str):
        self.path_for(key).unlink(missing_ok=True)


import asyncio
import hashlib
import tempfile
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.config import Config
from app.core.config import settings


AUDIO_SIGNATURES = {
    "audio/wav": lambda b: b[:4] == b"RIFF" and b[8:12] == b"WAVE",
    "audio/webm": lambda b: b[:4] == b"\x1a\x45\xdf\xa3",
    "audio/ogg": lambda b: b[:4] == b"OggS",
    "audio/mpeg": lambda b: b[:3] == b"ID3" or (
        len(b) >= 2 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0
    ),
    "audio/mp4": lambda b: len(b) >= 12 and b[4:8] == b"ftyp",
    "audio/x-m4a": lambda b: len(b) >= 12 and b[4:8] == b"ftyp",
}


class R2PrivateStorage:
    def __init__(self):
        required = {
            "R2_ACCOUNT_ID": settings.r2_account_id,
            "R2_ACCESS_KEY_ID": settings.r2_access_key_id,
            "R2_SECRET_ACCESS_KEY": settings.r2_secret_access_key,
            "R2_BUCKET_NAME": settings.r2_bucket_name,
        }

        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                "Missing R2 configuration: " + ", ".join(missing)
            )

        endpoint = settings.r2_endpoint_url or (
            f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
        )

        self.bucket = settings.r2_bucket_name

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name=settings.r2_region,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )

    async def save_upload(self, upload, key: str, max_bytes: int):
        total = 0
        digest = hashlib.sha256()

        # Avoid keeping large recordings entirely in RAM.
        with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as temp:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break

                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("File exceeds configured upload limit")

                digest.update(chunk)
                temp.write(chunk)

            if total == 0:
                raise ValueError("Empty recording")

            temp.seek(0)

            await asyncio.to_thread(
                self.client.upload_fileobj,
                temp,
                self.bucket,
                key,
                ExtraArgs={
                    "ContentType": upload.content_type or "application/octet-stream"
                },
            )

        return total, digest.hexdigest(), key

    def validate_audio_header(self, key: str, mime_type: str) -> bool:
        validator = AUDIO_SIGNATURES.get(mime_type)
        if not validator:
            return False

        response = self.client.get_object(
            Bucket=self.bucket,
            Key=key,
            Range="bytes=0-63",
        )

        try:
            header = response["Body"].read(64)
        finally:
            response["Body"].close()

        return bool(validator(header))

    async def save_bytes(self, key: str, data: bytes, content_type: str) -> None:
        await asyncio.to_thread(
            self.client.put_object,
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    def open(self, key: str):
        response = self.client.get_object(
            Bucket=self.bucket,
            Key=key,
        )
        return response["Body"]

    def delete(self, key: str):
        self.client.delete_object(
            Bucket=self.bucket,
            Key=key,
        )

    def download_to_path(self, key: str, destination: Path):
        destination.parent.mkdir(parents=True, exist_ok=True)

        self.client.download_file(
            self.bucket,
            key,
            str(destination),
        )

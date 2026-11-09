
from app.core.config import settings
from app.services.storage.local import LocalPrivateStorage
from app.services.storage.r2 import R2PrivateStorage


def get_storage():
    provider = settings.storage_provider.strip().lower()

    if provider == "local":
        return LocalPrivateStorage()

    if provider == "r2":
        return R2PrivateStorage()

    raise ValueError(
        f"Unsupported storage provider: {provider}"
    )

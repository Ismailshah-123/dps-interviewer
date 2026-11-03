import os
os.environ["DPS_ENV_FILE"] = ""  # never read the developer's backend/.env during tests
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-tests-123456"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_dps.db"
os.environ["STORAGE_ROOT"] = "./test_storage"
os.environ["DEFAULT_ADMIN_PASSWORD"] = "TestPassword123!"
os.environ["TRANSCRIPTION_PROVIDER"] = "unavailable"
os.environ["SUMMARIZATION_PROVIDER"] = "unavailable"
import pytest

@pytest.fixture
async def client():
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c

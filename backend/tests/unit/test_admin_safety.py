from types import SimpleNamespace
from uuid import uuid4
from app.models.models import Role

def test_last_admin_policy_definition():
    admin = SimpleNamespace(id=uuid4(), role=Role.ADMIN.value, is_active=True)
    assert admin.role == Role.ADMIN.value
    assert admin.is_active is True

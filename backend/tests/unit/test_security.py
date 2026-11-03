from uuid import uuid4
from datetime import timedelta
import pytest
from app.core.security import hash_password, verify_password, create_token, decode_token

def test_password_hash_roundtrip():
    password='Strong-Test-Password-123!'
    hashed=hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password('wrong', hashed)

def test_token_type_and_subject():
    uid=uuid4(); token=create_token(uid,'access',timedelta(minutes=5)); payload=decode_token(token,'access')
    assert payload['sub']==str(uid)
    with pytest.raises(ValueError): decode_token(token,'refresh')

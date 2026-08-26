import os

os.environ.setdefault("AUTH_SECRET", "ci-test-secret")

from app.owned_auth import _digest, _otp_hash


def test_digest_is_stable_and_nonreversible_shape():
    value = _digest("session-token")
    assert len(value) == 32
    assert value == _digest("session-token")
    assert value != _digest("different-token")


def test_otp_hash_binds_email_and_code():
    a = _otp_hash("user@gmail.com", "123456")
    assert len(a) == 32
    assert a == _otp_hash("user@gmail.com", "123456")
    assert a != _otp_hash("other@gmail.com", "123456")
    assert a != _otp_hash("user@gmail.com", "654321")

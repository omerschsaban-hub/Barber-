import os

os.environ.setdefault("AUTH_SECRET", "ci-test-secret-with-at-least-32-bytes")

import pytest
from fastapi import HTTPException

from app.owned_auth import _bearer, _digest, _normalize_email, _otp_hash


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


def test_email_normalization_is_case_insensitive_and_rejects_non_gmail():
    assert _normalize_email("  User@gmail.com ") == "user@gmail.com"
    with pytest.raises(HTTPException) as exc:
        _normalize_email("user@example.com")
    assert exc.value.status_code == 400


def test_bearer_precedence_and_cookie_fallback():
    class Request:
        headers = {"authorization": "Bearer header-token"}
        cookies = {"fabrient_session": "cookie-token"}

    assert _bearer(Request(), "Bearer explicit-token") == "explicit-token"
    assert _bearer(Request(), None) == "header-token"

    class CookieOnly:
        headers = {}
        cookies = {"fabrient_session": "cookie-token"}

    assert _bearer(CookieOnly(), None) == "cookie-token"


def test_bearer_rejects_non_bearer_authorization():
    class Request:
        headers = {"authorization": "Basic abc"}
        cookies = {}

    assert _bearer(Request(), None) is None

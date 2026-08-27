import pytest
from pydantic import ValidationError

from src.auth.schemas import LoginRequest, SignupRequest, VerifyRequest

VALID_SIGNUP = {
    "name": "홍길동",
    "email": "user@example.com",
    "password": "Passw0rd!",
    "phone": "010-1234-5678",
}


def test_signup_request_accepts_valid_payload():
    req = SignupRequest(**VALID_SIGNUP)
    assert req.email == "user@example.com"
    assert req.phone == "010-1234-5678"


def test_signup_request_rejects_blank_name():
    with pytest.raises(ValidationError):
        SignupRequest(**{**VALID_SIGNUP, "name": "   "})


@pytest.mark.parametrize(
    "password",
    [
        "Sh0rt!",  # 7자 (길이 미달)
        "alllowercase1",  # 2종류만 조합 (소문자+숫자)
        "ALLUPPERCASE!",  # 2종류만 조합 (대문자+특수문자)
    ],
)
def test_signup_request_rejects_weak_password(password):
    with pytest.raises(ValidationError):
        SignupRequest(**{**VALID_SIGNUP, "password": password})


@pytest.mark.parametrize("phone", ["010123456", "010-123-456", "02-1234-5678"])
def test_signup_request_rejects_invalid_phone(phone):
    with pytest.raises(ValidationError):
        SignupRequest(**{**VALID_SIGNUP, "phone": phone})


def test_verify_request_rejects_non_six_digit_code():
    with pytest.raises(ValidationError):
        VerifyRequest(email="user@example.com", code="12345")


def test_login_request_rejects_empty_password():
    with pytest.raises(ValidationError):
        LoginRequest(email="user@example.com", password="")

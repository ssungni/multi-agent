import fakeredis
import pytest

from src.auth.constants import MAX_LOGIN_FAILS, MAX_VERIFY_ATTEMPTS, UserStatus
from src.auth.exceptions import (
    AccountLockedError,
    AlreadyVerifiedError,
    EmailDuplicateError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    PhoneDuplicateError,
    SignupNotFoundError,
    TooManyRequestsError,
    VerifyCodeExpiredError,
    VerifyCodeMismatchError,
)
from src.auth.schemas import LoginRequest, SignupRequest, VerifyRequest
from src.auth.service import AuthService, _verify_code_key

VALID_SIGNUP = {
    "name": "홍길동",
    "email": "user@example.com",
    "password": "Passw0rd!",
    "phone": "010-1234-5678",
}


@pytest.fixture
def redis_client():
    client = fakeredis.FakeRedis(decode_responses=True)
    yield client
    client.flushall()


@pytest.fixture
def service(db_session, redis_client):
    return AuthService(db_session, redis_client)


def signup_and_verify(service, redis_client, **overrides):
    payload = {**VALID_SIGNUP, **overrides}
    service.signup(SignupRequest(**payload))
    code = redis_client.get(_verify_code_key(payload["email"]))
    token_response, refresh_token = service.verify_email(
        VerifyRequest(email=payload["email"], code=code)
    )
    return token_response, refresh_token


def test_signup_creates_pending_user_and_verification_code(service, redis_client):
    service.signup(SignupRequest(**VALID_SIGNUP))
    user = service.repo.get_by_email(VALID_SIGNUP["email"])
    assert user.status == UserStatus.PENDING.value
    assert redis_client.get(_verify_code_key(VALID_SIGNUP["email"])) is not None


def test_signup_duplicate_active_email_rejected(service):
    signup_and_verify(service, service.redis)
    with pytest.raises(EmailDuplicateError):
        service.signup(SignupRequest(**{**VALID_SIGNUP, "phone": "010-9999-0000"}))


def test_signup_duplicate_phone_rejected(service):
    service.signup(SignupRequest(**VALID_SIGNUP))
    with pytest.raises(PhoneDuplicateError):
        service.signup(SignupRequest(**{**VALID_SIGNUP, "email": "other@example.com"}))


def test_signup_resend_while_pending_does_not_raise(service):
    service.signup(SignupRequest(**VALID_SIGNUP))
    service.signup(SignupRequest(**VALID_SIGNUP))  # 같은 이메일로 PENDING 상태 재시도
    user = service.repo.get_by_email(VALID_SIGNUP["email"])
    assert user.status == UserStatus.PENDING.value


def test_verify_wrong_code_raises_and_counts_attempts(service, redis_client):
    service.signup(SignupRequest(**VALID_SIGNUP))
    for _ in range(MAX_VERIFY_ATTEMPTS - 1):
        with pytest.raises(VerifyCodeMismatchError):
            service.verify_email(VerifyRequest(email=VALID_SIGNUP["email"], code="000000"))
    assert redis_client.get(_verify_code_key(VALID_SIGNUP["email"])) is not None

    with pytest.raises(VerifyCodeMismatchError):
        service.verify_email(VerifyRequest(email=VALID_SIGNUP["email"], code="000000"))
    # 시도 횟수 초과 시 코드 자체가 폐기됨
    assert redis_client.get(_verify_code_key(VALID_SIGNUP["email"])) is None


def test_verify_missing_code_raises_expired(service):
    with pytest.raises(VerifyCodeExpiredError):
        service.verify_email(VerifyRequest(email="nobody@example.com", code="123456"))


def test_verify_success_activates_user_and_returns_tokens(service, redis_client):
    token_response, refresh_token = signup_and_verify(service, redis_client)
    assert token_response.user.email == VALID_SIGNUP["email"]
    assert refresh_token
    assert service.repo.get_by_email(VALID_SIGNUP["email"]).status == UserStatus.ACTIVE.value


def test_verify_already_active_rejected(service, redis_client):
    signup_and_verify(service, redis_client)
    # signup/resend는 이미 ACTIVE인 계정에 새 코드 발급을 막지만, 동시 verify 요청이
    # 코드를 아직 지우기 전에 몰리는 레이스 상황은 남아 있어 그 분기를 직접 재현한다.
    redis_client.set(_verify_code_key(VALID_SIGNUP["email"]), "999999", ex=300)
    with pytest.raises(AlreadyVerifiedError):
        service.verify_email(VerifyRequest(email=VALID_SIGNUP["email"], code="999999"))


def test_resend_respects_cooldown(service):
    service.signup(SignupRequest(**VALID_SIGNUP))
    with pytest.raises(TooManyRequestsError):
        service.resend_verification(VALID_SIGNUP["email"])


def test_resend_unknown_email_raises_not_found(service):
    with pytest.raises(SignupNotFoundError):
        service.resend_verification("nobody@example.com")


def test_login_success_returns_tokens(service, redis_client):
    signup_and_verify(service, redis_client)
    token_response, refresh_token = service.login(
        LoginRequest(email=VALID_SIGNUP["email"], password=VALID_SIGNUP["password"])
    )
    assert token_response.user.email == VALID_SIGNUP["email"]
    assert refresh_token
    assert service.repo.get_by_email(VALID_SIGNUP["email"]).last_login_at is not None


def test_login_pending_user_rejected(service):
    service.signup(SignupRequest(**VALID_SIGNUP))
    with pytest.raises(EmailNotVerifiedError):
        service.login(LoginRequest(email=VALID_SIGNUP["email"], password=VALID_SIGNUP["password"]))


def test_login_wrong_password_raises_and_counts_failures(service):
    signup_and_verify(service, service.redis)
    for _ in range(MAX_LOGIN_FAILS):
        with pytest.raises(InvalidCredentialsError):
            service.login(LoginRequest(email=VALID_SIGNUP["email"], password="WrongPass1!"))

    with pytest.raises(AccountLockedError):
        service.login(LoginRequest(email=VALID_SIGNUP["email"], password=VALID_SIGNUP["password"]))


def test_refresh_rotates_token_and_invalidates_old_one(service, redis_client):
    _, refresh_token = signup_and_verify(service, redis_client)

    new_access_token, new_refresh_token = service.refresh(refresh_token)
    assert new_access_token
    assert new_refresh_token != refresh_token

    with pytest.raises(InvalidRefreshTokenError):
        service.refresh(refresh_token)  # 이미 회전되어 재사용 불가


def test_logout_invalidates_refresh_token(service, redis_client):
    _, refresh_token = signup_and_verify(service, redis_client)
    service.logout(refresh_token)
    with pytest.raises(InvalidRefreshTokenError):
        service.refresh(refresh_token)

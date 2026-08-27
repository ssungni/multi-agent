from redis import Redis
from sqlalchemy.orm import Session

from src.auth.constants import (
    ACCESS_TOKEN_TTL_SECONDS,
    LOGIN_FAIL_TTL_SECONDS,
    MAX_LOGIN_FAILS,
    MAX_VERIFY_ATTEMPTS,
    REFRESH_TOKEN_TTL_SECONDS,
    RESEND_COOLDOWN_SECONDS,
    UserStatus,
    VERIFY_CODE_TTL_SECONDS,
)
from src.auth.email_service import EmailService
from src.auth.exceptions import (
    AccountLockedError,
    AccountSuspendedError,
    AccountWithdrawnError,
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
from src.auth.models import User
from src.auth.repository import UserRepository
from src.auth.schemas import (
    LoginRequest,
    ResendResponse,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    UserPublic,
    VerifyRequest,
)
from src.auth.utils import (
    TokenDecodeError,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_verification_code,
    hash_password,
    verify_password,
)


def _verify_code_key(email: str) -> str:
    return f"signup:verify:{email}"


def _verify_attempts_key(email: str) -> str:
    return f"signup:verify:attempts:{email}"


def _resend_cooldown_key(email: str) -> str:
    return f"signup:verify:cooldown:{email}"


def _login_fail_key(email: str) -> str:
    return f"login_fail:{email}"


def _refresh_token_key(jti: str) -> str:
    return f"refresh_token:{jti}"


class AuthService:
    def __init__(self, db: Session, redis: Redis, email_service: EmailService | None = None):
        self.db = db
        self.redis = redis
        self.repo = UserRepository(db)
        self.email_service = email_service or EmailService()

    def signup(self, req: SignupRequest) -> SignupResponse:
        existing_by_email = self.repo.get_by_email(req.email)
        if existing_by_email and existing_by_email.status == UserStatus.ACTIVE.value:
            raise EmailDuplicateError()

        existing_by_phone = self.repo.get_by_phone(req.phone)
        if existing_by_phone and (
            existing_by_email is None or existing_by_phone.id != existing_by_email.id
        ):
            raise PhoneDuplicateError()

        password_hash = hash_password(req.password)
        if existing_by_email is None:
            self.repo.create(
                name=req.name, email=req.email, phone=req.phone, password_hash=password_hash
            )
        else:
            existing_by_email.name = req.name
            existing_by_email.phone = req.phone
            existing_by_email.password_hash = password_hash
            self.db.flush()

        self._issue_verification_code(req.email)
        return SignupResponse(message="인증코드를 이메일로 발송했습니다.", email=req.email)

    def resend_verification(self, email: str) -> ResendResponse:
        if self.redis.exists(_resend_cooldown_key(email)):
            raise TooManyRequestsError()

        user = self.repo.get_by_email(email)
        if user is None:
            raise SignupNotFoundError()
        if user.status == UserStatus.ACTIVE.value:
            raise AlreadyVerifiedError()

        self._issue_verification_code(email)
        return ResendResponse(message="인증코드를 재발송했습니다.")

    def verify_email(self, req: VerifyRequest) -> tuple[TokenResponse, str]:
        code_key = _verify_code_key(req.email)
        attempts_key = _verify_attempts_key(req.email)

        stored_code = self.redis.get(code_key)
        if stored_code is None:
            raise VerifyCodeExpiredError()

        if stored_code != req.code:
            attempts = self.redis.incr(attempts_key)
            self.redis.expire(attempts_key, VERIFY_CODE_TTL_SECONDS)
            if attempts >= MAX_VERIFY_ATTEMPTS:
                self.redis.delete(code_key, attempts_key)
            raise VerifyCodeMismatchError()

        user = self.repo.get_by_email(req.email)
        if user is None:
            raise SignupNotFoundError()
        if user.status == UserStatus.ACTIVE.value:
            raise AlreadyVerifiedError()

        self.repo.update_status(user, UserStatus.ACTIVE.value)
        self.redis.delete(code_key, attempts_key)

        return self._issue_tokens(user)

    def login(self, req: LoginRequest) -> tuple[TokenResponse, str]:
        fail_key = _login_fail_key(req.email)
        fail_count = int(self.redis.get(fail_key) or 0)
        if fail_count >= MAX_LOGIN_FAILS:
            raise AccountLockedError()

        user = self.repo.get_by_email(req.email)
        if user is None or not verify_password(req.password, user.password_hash):
            pipe = self.redis.pipeline()
            pipe.incr(fail_key)
            pipe.expire(fail_key, LOGIN_FAIL_TTL_SECONDS)
            pipe.execute()
            raise InvalidCredentialsError()

        if user.status == UserStatus.PENDING.value:
            raise EmailNotVerifiedError()
        if user.status == UserStatus.SUSPENDED.value:
            raise AccountSuspendedError()
        if user.status == UserStatus.WITHDRAWN.value:
            raise AccountWithdrawnError()

        self.redis.delete(fail_key)
        self.repo.update_last_login(user)
        return self._issue_tokens(user)

    def refresh(self, refresh_token: str | None) -> tuple[str, str]:
        if not refresh_token:
            raise InvalidRefreshTokenError()
        try:
            payload = decode_token(refresh_token)
        except TokenDecodeError as exc:
            raise InvalidRefreshTokenError() from exc

        if payload.get("type") != "refresh":
            raise InvalidRefreshTokenError()

        jti = payload["jti"]
        user_id = self.redis.get(_refresh_token_key(jti))
        if user_id is None:
            raise InvalidRefreshTokenError()

        self.redis.delete(_refresh_token_key(jti))

        user = self.repo.get_by_id(int(user_id))
        if user is None or user.status != UserStatus.ACTIVE.value:
            raise InvalidRefreshTokenError()

        access_token = create_access_token(user.id)
        new_refresh_token, new_jti = create_refresh_token(user.id)
        self.redis.set(_refresh_token_key(new_jti), str(user.id), ex=REFRESH_TOKEN_TTL_SECONDS)
        return access_token, new_refresh_token

    def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        try:
            payload = decode_token(refresh_token)
        except TokenDecodeError:
            return
        jti = payload.get("jti")
        if jti:
            self.redis.delete(_refresh_token_key(jti))

    def _issue_verification_code(self, email: str) -> None:
        code = generate_verification_code()
        self.redis.set(_verify_code_key(email), code, ex=VERIFY_CODE_TTL_SECONDS)
        self.redis.set(_resend_cooldown_key(email), "1", ex=RESEND_COOLDOWN_SECONDS)
        self.email_service.send_verification_code(email, code)

    def _issue_tokens(self, user: User) -> tuple[TokenResponse, str]:
        access_token = create_access_token(user.id)
        refresh_token, jti = create_refresh_token(user.id)
        self.redis.set(_refresh_token_key(jti), str(user.id), ex=REFRESH_TOKEN_TTL_SECONDS)
        response = TokenResponse(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_TTL_SECONDS,
            user=UserPublic.model_validate(user),
        )
        return response, refresh_token

import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from src.auth.constants import ACCESS_TOKEN_TTL_SECONDS, REFRESH_TOKEN_TTL_SECONDS
from src.core.config import settings


class TokenDecodeError(Exception):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def generate_verification_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(6))


def _create_token(user_id: int, token_type: str, ttl_seconds: int) -> tuple[str, str]:
    jti = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": now + timedelta(seconds=ttl_seconds),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def create_access_token(user_id: int) -> str:
    token, _ = _create_token(user_id, "access", ACCESS_TOKEN_TTL_SECONDS)
    return token


def create_refresh_token(user_id: int) -> tuple[str, str]:
    return _create_token(user_id, "refresh", REFRESH_TOKEN_TTL_SECONDS)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise TokenDecodeError() from exc

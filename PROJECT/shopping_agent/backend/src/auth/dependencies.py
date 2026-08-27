from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session

from src.auth.constants import UserStatus
from src.auth.exceptions import AccountSuspendedError, AccountWithdrawnError, InvalidAccessTokenError
from src.auth.models import User
from src.auth.repository import UserRepository
from src.auth.service import AuthService
from src.auth.utils import TokenDecodeError, decode_token
from src.core.database import get_db
from src.core.redis import get_redis

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_db), redis: Redis = Depends(get_redis)) -> AuthService:
    return AuthService(db, redis)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise InvalidAccessTokenError()

    try:
        payload = decode_token(credentials.credentials)
    except TokenDecodeError as exc:
        raise InvalidAccessTokenError() from exc

    if payload.get("type") != "access":
        raise InvalidAccessTokenError()

    user = UserRepository(db).get_by_id(int(payload["sub"]))
    if user is None:
        raise InvalidAccessTokenError()
    if user.status == UserStatus.SUSPENDED.value:
        raise AccountSuspendedError()
    if user.status == UserStatus.WITHDRAWN.value:
        raise AccountWithdrawnError()
    return user

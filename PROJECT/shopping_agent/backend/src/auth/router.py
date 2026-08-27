from fastapi import APIRouter, Cookie, Depends, Response
from pydantic import EmailStr

from src.auth.constants import ACCESS_TOKEN_TTL_SECONDS, REFRESH_TOKEN_TTL_SECONDS, UserStatus
from src.auth.dependencies import get_auth_service, get_current_user
from src.auth.models import User
from src.auth.schemas import (
    AvailabilityResponse,
    LoginRequest,
    LogoutResponse,
    RefreshResponse,
    ResendRequest,
    ResendResponse,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    UserMeResponse,
    VerifyRequest,
)
from src.auth.service import AuthService
from src.core.config import settings

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth"

router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=REFRESH_TOKEN_TTL_SECONDS,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
    )


@router.post("/signup", response_model=SignupResponse, status_code=201)
def signup(req: SignupRequest, service: AuthService = Depends(get_auth_service)):
    return service.signup(req)


@router.post("/signup/verify", response_model=TokenResponse)
def verify_signup(
    req: VerifyRequest, response: Response, service: AuthService = Depends(get_auth_service)
):
    token_response, refresh_token = service.verify_email(req)
    _set_refresh_cookie(response, refresh_token)
    return token_response


@router.post("/signup/resend", response_model=ResendResponse)
def resend_signup_code(req: ResendRequest, service: AuthService = Depends(get_auth_service)):
    return service.resend_verification(req.email)


@router.get("/check-email", response_model=AvailabilityResponse)
def check_email(email: EmailStr, service: AuthService = Depends(get_auth_service)):
    user = service.repo.get_by_email(email)
    available = user is None or user.status != UserStatus.ACTIVE.value
    return AvailabilityResponse(available=available)


@router.get("/check-phone", response_model=AvailabilityResponse)
def check_phone(phone: str, service: AuthService = Depends(get_auth_service)):
    return AvailabilityResponse(available=service.repo.get_by_phone(phone) is None)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, response: Response, service: AuthService = Depends(get_auth_service)):
    token_response, refresh_token = service.login(req)
    _set_refresh_cookie(response, refresh_token)
    return token_response


@router.post("/refresh", response_model=RefreshResponse)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    service: AuthService = Depends(get_auth_service),
):
    access_token, new_refresh_token = service.refresh(refresh_token)
    _set_refresh_cookie(response, new_refresh_token)
    return RefreshResponse(access_token=access_token, expires_in=ACCESS_TOKEN_TTL_SECONDS)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    service: AuthService = Depends(get_auth_service),
):
    service.logout(refresh_token)
    response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    return LogoutResponse(message="로그아웃되었습니다.")


@users_router.get("/me", response_model=UserMeResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

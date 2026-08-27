import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.auth.constants import UserStatus

PHONE_REGEX = re.compile(r"^01[016789]-?\d{3,4}-?\d{4}$")


def validate_password_policy(password: str) -> str:
    if not (8 <= len(password) <= 64):
        raise ValueError("비밀번호는 8자 이상 64자 이하여야 합니다.")
    categories = [
        bool(re.search(r"[a-z]", password)),
        bool(re.search(r"[A-Z]", password)),
        bool(re.search(r"\d", password)),
        bool(re.search(r"[^a-zA-Z0-9]", password)),
    ]
    if sum(categories) < 3:
        raise ValueError("비밀번호는 대문자/소문자/숫자/특수문자 중 3종류 이상을 포함해야 합니다.")
    return password


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str
    phone: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("이름은 공백일 수 없습니다.")
        return v

    @field_validator("password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        return validate_password_policy(v)

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str) -> str:
        if not PHONE_REGEX.match(v):
            raise ValueError("올바른 휴대폰 번호 형식이 아닙니다.")
        return v


class SignupResponse(BaseModel):
    message: str
    email: EmailStr


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")


class ResendRequest(BaseModel):
    email: EmailStr


class ResendResponse(BaseModel):
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    email: EmailStr


class UserMeResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    email: EmailStr
    phone: str
    status: UserStatus
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserPublic


class RefreshResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class LogoutResponse(BaseModel):
    message: str


class AvailabilityResponse(BaseModel):
    available: bool

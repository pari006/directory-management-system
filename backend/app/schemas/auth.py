from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.user import UserOut, MAX_PASSWORD_BYTES


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(
                "Password is too long; use at most 72 UTF-8 bytes."
            )
        return value


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserOut] = None


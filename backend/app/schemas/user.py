from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

MAX_PASSWORD_BYTES = 72


class UserSignup(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: str = Field(min_length=8, max_length=64)
    role: Optional[str] = "USER"

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(
                "Password is too long; use at most 72 UTF-8 bytes."
            )
        return value

    @field_validator("role")
    @classmethod
    def normalize_role(cls, value: Optional[str]) -> str:
        if value is None:
            return "USER"
        val = value.upper()
        if val not in ("ADMIN", "USER"):
            raise ValueError("role must be either 'ADMIN' or 'USER'")
        return val


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: str

    model_config = {"from_attributes": True}


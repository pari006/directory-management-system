from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

import bcrypt
from jose import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import settings

password_hasher = PasswordHasher()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        pass

    if hashed_password.startswith("$2"):
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except ValueError:
            return False
    return False


def get_password_hash(password: str) -> str:
    return password_hasher.hash(password)


def create_access_token(
    subject: str,
    role: str,
    company_id: Optional[UUID] = None,
    expires_delta: Optional[timedelta] = None,
    extra: dict[str, Any] | None = None,
) -> str:
    """
    Create JWT access token.
    For Super Admin: company_id should be None.
    For Company Admin/Employee: company_id should be their tenant UUID.
    Extra can include additional claims such as employee_id.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
    }
    if company_id:
        to_encode["company_id"] = str(company_id)
    if extra:
        to_encode.update(extra)
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify JWT token."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


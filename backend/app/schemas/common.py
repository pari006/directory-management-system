from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str

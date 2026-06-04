from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.database_models import EmployeeRole


class EmployeeBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    role: EmployeeRole = EmployeeRole.EMPLOYEE


class EmployeeCreate(EmployeeBase):
    leaves_allowed: Optional[int] = Field(None, ge=0)
    base_salary: Optional[float] = Field(None, gt=0)
    payment_date: Optional[int] = Field(None, ge=1, le=31)


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=120)
    last_name: Optional[str] = Field(None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    role: Optional[EmployeeRole] = None
    base_salary: Optional[float] = Field(None, gt=0)
    payment_date: Optional[int] = Field(None, ge=1, le=31)
    leaves_allowed: Optional[int] = Field(None, ge=0)


class EmployeeOut(EmployeeBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime
    base_salary: Optional[float] = None
    payment_date: Optional[int] = None
    leaves_allowed: Optional[int] = None
    leaves_taken: Optional[int] = None

    model_config = {"from_attributes": True}


class EmployeeListPayload(BaseModel):
    items: list[EmployeeOut]
    total: int


class UserAuthBase(BaseModel):
    email: EmailStr
    role: Literal["ADMIN", "USER"] = "USER"


class UserAuthCreate(UserAuthBase):
    password: str = Field(min_length=8, max_length=64)
    username: Optional[str] = Field(None, min_length=3, max_length=50)


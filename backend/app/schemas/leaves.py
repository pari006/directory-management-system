from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.database_models import LeaveRequestStatus


class LeaveRequestCreate(BaseModel):
    start_date: date = Field(..., description="Start date of leave")
    end_date: date = Field(..., description="End date of leave")
    reason: str | None = Field(None, max_length=500, description="Reason for leave request")

    model_config = {"json_schema_extra": {"example": {
        "start_date": "2026-06-15",
        "end_date": "2026-06-20",
        "reason": "Vacation"
    }}}


class LeaveRequestResponse(BaseModel):
    id: UUID
    employee_id: UUID
    start_date: date
    end_date: date
    reason: str | None
    status: LeaveRequestStatus
    created_at: str
    employee_name: str | None = None
    employee_email: str | None = None

    model_config = {"from_attributes": True}


class LeaveApprovalSchema(BaseModel):
    status: LeaveRequestStatus = Field(..., description="Approval status (APPROVED or REJECTED)")

    model_config = {"json_schema_extra": {"example": {
        "status": "APPROVED"
    }}}


class LeaveBalanceResponse(BaseModel):
    id: UUID
    employee_id: UUID
    leaves_allowed: int
    leaves_taken: int
    available_balance: int

    model_config = {"from_attributes": True}

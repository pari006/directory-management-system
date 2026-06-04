from uuid import UUID
from pydantic import BaseModel, Field


class PayrollSummaryResponse(BaseModel):
    company_id: UUID
    headcount: int = Field(..., description="Total number of employees")
    total_payroll_overhead: float = Field(..., description="Total upcoming payroll in currency units")

    model_config = {"json_schema_extra": {"example": {
        "company_id": "550e8400-e29b-41d4-a716-446655440000",
        "headcount": 25,
        "total_payroll_overhead": 500000.00
    }}}


from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_company_admin, get_db
from app.models.database_models import Employee, Compensation
from app.schemas.payroll import PayrollSummaryResponse
from app.core.exceptions import CompanyNotFound, TenantIsolationError

router = APIRouter(prefix="/payroll", tags=["Payroll"])

@router.get(
    "/summary",
    response_model=PayrollSummaryResponse,
    summary="Get payroll summary for company",
)
async def get_payroll_summary(
    current_admin: Employee = Depends(require_company_admin),
    db: AsyncSession = Depends(get_db),
) -> PayrollSummaryResponse:
    """
    Get payroll summary for the company.

    Returns:
    - headcount: Total number of active employees
    - total_payroll_overhead: Sum of all base salaries

    Only accessible to Company Admin for their company.
    """
    company_id = current_admin.company_id

    stmt_head = select(func.count(Employee.id)).where(Employee.company_id == company_id)
    res_head = await db.execute(stmt_head)
    headcount_result = res_head.scalar_one()

    subquery = select(Employee.id).where(Employee.company_id == company_id)
    stmt_sum = select(func.coalesce(func.sum(Compensation.base_salary), 0)).where(Compensation.employee_id.in_(subquery))
    res_sum = await db.execute(stmt_sum)
    total_payroll = res_sum.scalar_one()

    return PayrollSummaryResponse(
        company_id=company_id,
        headcount=int(headcount_result or 0),
        total_payroll_overhead=float(total_payroll or 0),
    )

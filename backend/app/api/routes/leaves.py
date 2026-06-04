from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_employee, require_company_admin, get_db
from app.models.database_models import (
    LeaveRequest,
    LeaveBalance,
    Employee,
    LeaveRequestStatus,
)
from app.schemas.leaves import (
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveApprovalSchema,
    LeaveBalanceResponse,
)
from app.core.exceptions import (
    InsufficientLeaveBalance,
    LeaveRequestNotFound,
    TenantIsolationError,
)

router = APIRouter(prefix="/leaves", tags=["Leaves"])


@router.post(
    "/request",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a leave request",
)
async def post_leave_request(
    leave_data: LeaveRequestCreate,
    current_employee: Employee = Depends(require_employee),
    db: AsyncSession = Depends(get_db),
) -> LeaveRequestResponse:
    """
    Submit a new leave request.

    - Validates date range (end_date >= start_date)
    - Locks leave_balance row for atomic update
    - Checks that leaves_allowed - leaves_taken covers the request
    - Creates leave_request with PENDING status

    Uses SERIALIZABLE transaction isolation to prevent race conditions.
    """
    if leave_data.end_date < leave_data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be >= start_date"
        )

    days_requested = (leave_data.end_date - leave_data.start_date).days + 1

    stmt = select(LeaveBalance).where(LeaveBalance.employee_id == current_employee.id).with_for_update()
    res = await db.execute(stmt)
    leave_balance = res.scalar_one_or_none()

    if not leave_balance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave balance not found for employee")

    available_leaves = leave_balance.leaves_allowed - leave_balance.leaves_taken
    if available_leaves < days_requested:
        raise InsufficientLeaveBalance(f"Insufficient leave balance. Available: {available_leaves}, Requested: {days_requested}")

    leave_request = LeaveRequest(
        employee_id=current_employee.id,
        start_date=leave_data.start_date,
        end_date=leave_data.end_date,
        reason=leave_data.reason,
        status=LeaveRequestStatus.PENDING,
    )

    db.add(leave_request)
    await db.flush()
    await db.refresh(leave_request)

    return LeaveRequestResponse(
        id=leave_request.id,
        employee_id=leave_request.employee_id,
        start_date=leave_request.start_date,
        end_date=leave_request.end_date,
        reason=leave_request.reason,
        status=leave_request.status,
        created_at=leave_request.created_at.isoformat(),
        employee_name=f"{current_employee.first_name} {current_employee.last_name}",
        employee_email=current_employee.email,
    )


@router.patch(
    "/{leave_request_id}/approve",
    response_model=LeaveRequestResponse,
    summary="Approve or reject a leave request",
)
async def patch_leave_approval(
    leave_request_id: UUID,
    approval_data: LeaveApprovalSchema,
    current_admin: Employee = Depends(require_company_admin),
    db: AsyncSession = Depends(get_db),
) -> LeaveRequestResponse:
    """
    Approve or reject a leave request.

    If approving:
    - Locks leave_request and leave_balance rows
    - Calculates days = (end_date - start_date).days + 1
    - Increments leaves_taken by calculated days
    - Updates leave_request status to APPROVED

    If rejecting:
    - Updates leave_request status to REJECTED

    Uses SERIALIZABLE transaction isolation.
    """
    stmt = select(LeaveRequest).where(LeaveRequest.id == leave_request_id).with_for_update()
    res = await db.execute(stmt)
    leave_request = res.scalar_one_or_none()

    if not leave_request:
        raise LeaveRequestNotFound()

    stmt_emp = select(Employee).where(Employee.id == leave_request.employee_id)
    res_emp = await db.execute(stmt_emp)
    employee = res_emp.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if employee.company_id != current_admin.company_id:
        raise TenantIsolationError("Cannot access leave requests from other companies")

    previous_status = leave_request.status

    if approval_data.status == LeaveRequestStatus.APPROVED and previous_status != LeaveRequestStatus.APPROVED:
        days_approved = (leave_request.end_date - leave_request.start_date).days + 1
        stmt_lb = select(LeaveBalance).where(LeaveBalance.employee_id == employee.id).with_for_update()
        res_lb = await db.execute(stmt_lb)
        leave_balance = res_lb.scalar_one_or_none()
        if leave_balance:
            leave_balance.leaves_taken += days_approved
            db.add(leave_balance)
    elif previous_status == LeaveRequestStatus.APPROVED and approval_data.status != LeaveRequestStatus.APPROVED:
        days_to_restore = (leave_request.end_date - leave_request.start_date).days + 1
        stmt_lb = select(LeaveBalance).where(LeaveBalance.employee_id == employee.id).with_for_update()
        res_lb = await db.execute(stmt_lb)
        leave_balance = res_lb.scalar_one_or_none()
        if leave_balance:
            leave_balance.leaves_taken = max(0, leave_balance.leaves_taken - days_to_restore)
            db.add(leave_balance)

    leave_request.status = approval_data.status
    db.add(leave_request)
    await db.flush()
    await db.refresh(leave_request)

    return LeaveRequestResponse(
        id=leave_request.id,
        employee_id=leave_request.employee_id,
        start_date=leave_request.start_date,
        end_date=leave_request.end_date,
        reason=leave_request.reason,
        status=leave_request.status,
        created_at=leave_request.created_at.isoformat(),
        employee_name=f"{employee.first_name} {employee.last_name}",
        employee_email=employee.email,
    )


@router.get(
    "/company",
    response_model=list[LeaveRequestResponse],
    summary="Get all leave requests for the company (admin only)",
)
async def get_company_leave_requests(
    current_admin: Employee = Depends(require_company_admin),
    db: AsyncSession = Depends(get_db),
) -> list[LeaveRequestResponse]:
    """Get all leave requests submitted by employees in this company."""
    stmt = select(LeaveRequest, Employee).join(Employee, LeaveRequest.employee_id == Employee.id).where(Employee.company_id == current_admin.company_id).order_by(LeaveRequest.created_at.desc())
    res = await db.execute(stmt)
    results = res.all()

    return [
        LeaveRequestResponse(
            id=r.id,
            employee_id=r.employee_id,
            start_date=r.start_date,
            end_date=r.end_date,
            reason=r.reason,
            status=r.status,
            created_at=r.created_at.isoformat(),
            employee_name=f"{emp.first_name} {emp.last_name}",
            employee_email=emp.email,
        )
        for r, emp in results
    ]


@router.get(
    "/my-requests",
    response_model=list[LeaveRequestResponse],
    summary="Get employee's own leave requests",
)
async def get_my_leave_requests(
    current_employee: Employee = Depends(require_employee),
    db: AsyncSession = Depends(get_db),
) -> list[LeaveRequestResponse]:
    """Get all leave requests submitted by the logged-in employee."""
    stmt = select(LeaveRequest).where(LeaveRequest.employee_id == current_employee.id).order_by(LeaveRequest.created_at.desc())
    res = await db.execute(stmt)
    requests = res.scalars().all()

    return [
        LeaveRequestResponse(
            id=r.id,
            employee_id=r.employee_id,
            start_date=r.start_date,
            end_date=r.end_date,
            reason=r.reason,
            status=r.status,
            created_at=r.created_at.isoformat(),
            employee_name=f"{current_employee.first_name} {current_employee.last_name}",
            employee_email=current_employee.email,
        )
        for r in requests
    ]


@router.get(
    "/{employee_id}/balance",
    response_model=LeaveBalanceResponse,
    summary="Get leave balance for an employee",
)
async def get_leave_balance(
    employee_id: UUID,
    current_employee: Employee = Depends(require_employee),
    db: AsyncSession = Depends(get_db),
) -> LeaveBalanceResponse:
    """Get leave balance for an employee (accessible to self or company admin)."""
    if current_employee.id != employee_id:
        if current_employee.role.value not in ["COMPANY_ADMIN", "SUPER_ADMIN"]:
            raise TenantIsolationError("Cannot access other employees' data")

    stmt = select(LeaveBalance).where(LeaveBalance.employee_id == employee_id)
    res = await db.execute(stmt)
    leave_balance = res.scalar_one_or_none()

    if not leave_balance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave balance not found")

    return LeaveBalanceResponse(
        id=leave_balance.id,
        employee_id=leave_balance.employee_id,
        leaves_allowed=leave_balance.leaves_allowed,
        leaves_taken=leave_balance.leaves_taken,
        available_balance=leave_balance.leaves_allowed - leave_balance.leaves_taken,
    )

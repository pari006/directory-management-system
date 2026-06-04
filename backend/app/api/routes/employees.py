from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, require_company_admin, require_employee
from app.models.database_models import Employee, LeaveBalance, Compensation
from app.schemas.common import APIResponse
from app.schemas.employee import EmployeeCreate, EmployeeListPayload, EmployeeOut, EmployeeUpdate
from app.core.exceptions import EmployeeNotFound

# Initialize the unified router
router = APIRouter(prefix="/employees", tags=["employees"])

# ==========================================
# INTERNAL UTILITY HELPERS
# ==========================================

async def _employee_by_email_company(db: AsyncSession, email: str, company_id: UUID):
    stmt = select(Employee).where(Employee.company_id == company_id, Employee.email == email)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def _employee_by_id(db: AsyncSession, employee_id: UUID, company_id: UUID = None):
    # Eager-load related rows to avoid lazy-load IO during serialization
    stmt = select(Employee).where(Employee.id == employee_id)
    if company_id:
        stmt = stmt.where(Employee.company_id == company_id)
    stmt = stmt.options(selectinload(Employee.compensation), selectinload(Employee.leave_balance))
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


# ==========================================
# ENDPOINTS / CONTROLLERS
# ==========================================


def _serialize_employee(emp: Employee, viewer_role: str) -> dict:
    comp = emp.__dict__.get('compensation')
    leave_bal = emp.__dict__.get('leave_balance')
    data = {
        "id": emp.id,
        "company_id": emp.company_id,
        "first_name": emp.first_name,
        "last_name": emp.last_name,
        "email": emp.email,
        "role": emp.role,
        "created_at": emp.created_at,
        "updated_at": emp.updated_at,
    }
    # Include compensation and leave details only for admin roles
    if viewer_role in ("SUPER_ADMIN", "COMPANY_ADMIN"):
        data.update({
            "base_salary": float(comp.base_salary) if comp and getattr(comp, 'base_salary', None) is not None else None,
            "payment_date": comp.payment_date if comp else None,
            "leaves_allowed": leave_bal.leaves_allowed if leave_bal else None,
            "leaves_taken": leave_bal.leaves_taken if leave_bal else None,
        })
    return data


async def _serialize_employee_by_id(db: AsyncSession, employee_id: UUID, company_id: UUID, viewer_role: str) -> EmployeeOut:
    employee = await _employee_by_id(db, employee_id, company_id=company_id)
    if not employee:
        raise EmployeeNotFound()
    return EmployeeOut.model_validate(_serialize_employee(employee, viewer_role))


@router.post(
    "",
    response_model=APIResponse[EmployeeOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create employee (Company Admin only)"
)
async def create_employee(
    payload: EmployeeCreate,
    current_admin: Employee = Depends(require_company_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new employee in the company with automatic leave and compensation structures."""


    try:
        employee = Employee(
            company_id=current_admin.company_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            role=payload.role,
        )
        db.add(employee)
        await db.flush()  # Generates the employee.id UUID instantly inside the database transaction

        if payload.leaves_allowed is not None:
            leave_balance = LeaveBalance(
                employee_id=employee.id,
                leaves_allowed=payload.leaves_allowed,
                leaves_taken=0
            )
            db.add(leave_balance)

        if payload.base_salary is not None:
            compensation = Compensation(
                employee_id=employee.id,
                base_salary=payload.base_salary,
                payment_date=payload.payment_date or 28
            )
            db.add(compensation)
                
        await db.flush()

    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or entity constraint violation encountered") from exc

    response_data = await _serialize_employee_by_id(db, employee.id, current_admin.company_id, current_admin.role.value)
    return APIResponse(message="Employee created successfully", data=response_data)


@router.get(
    "",
    response_model=APIResponse[EmployeeListPayload],
    summary="List employees"
)
async def list_employees(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str | None = None,
    sort_by: str = Query(default="first_name", pattern="^(first_name|last_name|email)$"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    current_employee: Employee = Depends(require_employee),
    db: AsyncSession = Depends(get_db),
):
    """List employees in the company. Enforces company_id isolation boundaries dynamically."""
    stmt = select(Employee).where(Employee.company_id == current_employee.company_id).options(selectinload(Employee.compensation), selectinload(Employee.leave_balance))
    
    if search:
        like_value = f"%{search}%"
        stmt = stmt.where(or_(
            Employee.first_name.ilike(like_value), 
            Employee.last_name.ilike(like_value), 
            Employee.email.ilike(like_value)
        ))

    sort_col = getattr(Employee, sort_by)
    if sort_order == "desc":
        sort_col = sort_col.desc()

    count_stmt = select(func.count()).select_from(Employee).where(Employee.company_id == current_employee.company_id)
    if search:
        like_value = f"%{search}%"
        count_stmt = count_stmt.where(or_(
            Employee.first_name.ilike(like_value),
            Employee.last_name.ilike(like_value),
            Employee.email.ilike(like_value),
        ))
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    stmt = stmt.order_by(sort_col).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    items = res.scalars().all()

    serialized = [_serialize_employee(e, current_employee.role) for e in items]

    return APIResponse(
        message="Employees fetched successfully",
        data=EmployeeListPayload(
            items=[EmployeeOut.model_validate(item) for item in serialized],
            total=total
        )
    )


@router.get(
    "/{employee_id}",
    response_model=APIResponse[EmployeeOut],
    summary="Get employee details"
)
async def get_employee(
    employee_id: UUID,
    current_employee: Employee = Depends(require_employee),
    db: AsyncSession = Depends(get_db),
):
    """Get employee details. Employees can view their own profile or peer details within their own tenant."""
    employee = await _employee_by_id(db, employee_id, company_id=current_employee.company_id)
    if not employee:
        raise EmployeeNotFound()
    serialized = _serialize_employee(employee, current_employee.role)
    return APIResponse(message="Employee fetched successfully", data=EmployeeOut.model_validate(serialized))


@router.put(
    "/{employee_id}",
    response_model=APIResponse[EmployeeOut],
    summary="Update employee (Company Admin only)"
)
async def update_employee(
    employee_id: UUID,
    payload: EmployeeUpdate,
    current_admin: Employee = Depends(require_company_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update employee details. Strictly isolated to Company Admin's matching company domain."""
    employee = await _employee_by_id(db, employee_id, company_id=current_admin.company_id)
    if not employee:
        raise EmployeeNotFound()

    updates = payload.model_dump(exclude_unset=True)
    base_salary = updates.pop("base_salary", None)
    payment_date = updates.pop("payment_date", None)
    leaves_allowed = updates.pop("leaves_allowed", None)

    for key, value in updates.items():
        setattr(employee, key, value)

    try:
        db.add(employee)

        if base_salary is not None or payment_date is not None:
            stmt_comp = select(Compensation).where(Compensation.employee_id == employee.id).with_for_update()
            res_comp = await db.execute(stmt_comp)
            compensation = res_comp.scalar_one_or_none()
            if compensation:
                if base_salary is not None:
                    compensation.base_salary = base_salary
                if payment_date is not None:
                    compensation.payment_date = payment_date
                db.add(compensation)
            else:
                compensation = Compensation(
                    employee_id=employee.id,
                    base_salary=base_salary if base_salary is not None else 50000.0,
                    payment_date=payment_date if payment_date is not None else 28
                )
                db.add(compensation)

        if leaves_allowed is not None:
            stmt_lb = select(LeaveBalance).where(LeaveBalance.employee_id == employee.id).with_for_update()
            res_lb = await db.execute(stmt_lb)
            leave_balance = res_lb.scalar_one_or_none()
            if leave_balance:
                leave_balance.leaves_allowed = leaves_allowed
                db.add(leave_balance)
            else:
                leave_balance = LeaveBalance(
                    employee_id=employee.id,
                    leaves_allowed=leaves_allowed,
                    leaves_taken=0
                )
                db.add(leave_balance)
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target modification triggers a data identity conflict") from exc

    await db.flush()
    response_data = await _serialize_employee_by_id(db, employee.id, current_admin.company_id, current_admin.role.value)
    return APIResponse(message="Employee updated successfully", data=response_data)


@router.delete(
    "/{employee_id}",
    response_model=APIResponse[dict],
    summary="Delete employee (Company Admin only)"
)
async def delete_employee(
    employee_id: UUID,
    current_admin: Employee = Depends(require_company_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete an employee permanently. Restrictive to Company Admins targeting their own tenants."""
    employee = await _employee_by_id(db, employee_id, company_id=current_admin.company_id)
    if not employee:
        raise EmployeeNotFound()

    await db.delete(employee)

    return APIResponse(message="Employee deleted successfully", data={"id": str(employee_id)})

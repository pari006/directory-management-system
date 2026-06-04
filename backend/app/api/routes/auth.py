from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.database_models import SuperAdmin, Employee, EmployeeRole, Company, SubscriptionStatus, LeaveBalance, Compensation
from app.schemas.auth import LoginRequest, TokenData
from app.schemas.common import APIResponse
from app.schemas.user import UserOut, UserSignup

router = APIRouter(prefix="/auth", tags=["auth"])


class CompanyRegisterRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8, max_length=64)
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)


@router.post(
    "/superadmin/login",
    response_model=APIResponse[TokenData],
    summary="Super Admin Login"
)
async def superadmin_login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login endpoint for Super Admins (platform owners)."""
    stmt = select(SuperAdmin).where(SuperAdmin.email == payload.email)
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession_a
    if isinstance(db, _AsyncSession_a):
        res = await db.execute(stmt)
    else:
        res = db.execute(stmt)
    admin = res.scalar_one_or_none()
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token(
        subject=admin.email,
        role=EmployeeRole.SUPER_ADMIN.value,
        company_id=None
    )
    user_out = UserOut(
        id=admin.id,
        email=admin.email,
        first_name="Super",
        last_name="Admin",
        role=EmployeeRole.SUPER_ADMIN.value
    )
    return APIResponse(
        message="Super admin login successful",
        data=TokenData(access_token=token, token_type="bearer", user=user_out),
    )


@router.post(
    "/company/login",
    response_model=APIResponse[TokenData],
    summary="Company Admin/Employee Login"
)
async def company_login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login endpoint for Company Admins and Employees (tenant users)."""
    stmt = select(Employee).where(Employee.email == payload.email)
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession_b
    if isinstance(db, _AsyncSession_b):
        res = await db.execute(stmt)
    else:
        res = db.execute(stmt)
    candidates = res.scalars().all()
    employee = next(
        (
            emp
            for emp in candidates
            if emp.password_hash and verify_password(payload.password, emp.password_hash)
        ),
        None,
    )
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    # enforce subscription status
    stmt_c = select(Company).where(Company.id == employee.company_id)
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession_b2
    if isinstance(db, _AsyncSession_b2):
        res_c = await db.execute(stmt_c)
    else:
        res_c = db.execute(stmt_c)
    company = res_c.scalar_one_or_none()
    if company and company.subscription_status == SubscriptionStatus.SUSPENDED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company subscription suspended; login blocked")

    token = create_access_token(subject=employee.email, role=employee.role.value, company_id=employee.company_id, extra={"employee_id": str(employee.id)})
    user_out = UserOut(
        id=employee.id,
        email=employee.email,
        first_name=employee.first_name,
        last_name=employee.last_name,
        role=employee.role.value
    )
    return APIResponse(
        message="Login successful",
        data=TokenData(access_token=token, token_type="bearer", user=user_out),
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenData],
    summary="Unified Login"
)
async def unified_login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Unified login for Super Admins, Company Admins, and Employees."""
    # 1. Try SuperAdmin
    stmt_sa = select(SuperAdmin).where(SuperAdmin.email == payload.email)
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession_c
    if isinstance(db, _AsyncSession_c):
        res_sa = await db.execute(stmt_sa)
    else:
        res_sa = db.execute(stmt_sa)
    admin = res_sa.scalar_one_or_none()
    if admin and verify_password(payload.password, admin.password_hash):
        token = create_access_token(
            subject=admin.email,
            role=EmployeeRole.SUPER_ADMIN.value,
            company_id=None
        )
        user_out = UserOut(
            id=admin.id,
            email=admin.email,
            first_name="Super",
            last_name="Admin",
            role=EmployeeRole.SUPER_ADMIN.value
        )
        return APIResponse(
            message="Super admin login successful",
            data=TokenData(access_token=token, token_type="bearer", user=user_out),
        )

    # 2. Try Employee
    stmt_emp = select(Employee).where(Employee.email == payload.email)
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession_d
    if isinstance(db, _AsyncSession_d):
        res_emp = await db.execute(stmt_emp)
    else:
        res_emp = db.execute(stmt_emp)
    employees = res_emp.scalars().all()
    employee = next(
        (
            emp
            for emp in employees
            if emp.password_hash and verify_password(payload.password, emp.password_hash)
        ),
        None,
    )
    if employee:
        # check company status
        stmt_c = select(Company).where(Company.id == employee.company_id)
        from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession_e
        if isinstance(db, _AsyncSession_e):
            res_c = await db.execute(stmt_c)
        else:
            res_c = db.execute(stmt_c)
        company = res_c.scalar_one_or_none()
        if company and company.subscription_status == SubscriptionStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company subscription suspended; login blocked"
            )

        token = create_access_token(subject=employee.email, role=employee.role.value, company_id=employee.company_id, extra={"employee_id": str(employee.id)})
        user_out = UserOut(
            id=employee.id,
            email=employee.email,
            first_name=employee.first_name,
            last_name=employee.last_name,
            role=employee.role.value
        )
        return APIResponse(
            message="Login successful",
            data=TokenData(access_token=token, token_type="bearer", user=user_out),
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )


@router.post(
    "/signup",
    response_model=APIResponse[TokenData],
    status_code=status.HTTP_201_CREATED,
    summary="Employee Signup (within a company)"
)
async def employee_signup(
    payload: UserSignup,
    company_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new employee within a company.

    Requires company_id in query parameters.
    """
    normalized_email = payload.email.lower()

    if company_id is None:
        stmt_global_exists = select(Employee).where(Employee.email == normalized_email)
        res_global_exists = await db.execute(stmt_global_exists)
        if res_global_exists.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use"
            )

    # If no company_id is provided, create a new company automatically for quick company-admin signups.
    if company_id is None:
        local_part, _, email_domain = normalized_email.partition("@")
        workspace_domain = normalized_email.replace("@", ".")
        company = Company(
            company_name=f"{local_part or 'default'} workspace",
            domain=workspace_domain or email_domain or None,
            subscription_status=SubscriptionStatus.ACTIVE
        )
        # Support both AsyncSession and regular Session used in tests
        from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession
        if isinstance(db, _AsyncSession):
            db.add(company)
            await db.flush()
        else:
            db.add(company)
            db.flush()
        company_id = company.id

    stmt_exists = select(Employee).where(Employee.email == normalized_email, Employee.company_id == company_id)
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession2
    if isinstance(db, _AsyncSession2):
        res_exists = await db.execute(stmt_exists)
        exists = res_exists.scalar_one_or_none()
    else:
        res_exists = db.execute(stmt_exists)
        exists = res_exists.scalar_one_or_none()

    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use for this company"
        )
    # Normalize names if missing
    default_name = normalized_email.split("@")[0] if "@" in normalized_email else "User"
    first_name = payload.first_name or default_name
    last_name = payload.last_name or ""

    # Determine role
    role_to_assign = EmployeeRole.COMPANY_ADMIN if payload.role == "ADMIN" else EmployeeRole.EMPLOYEE

    employee = Employee(
        company_id=company_id,
        first_name=first_name,
        last_name=last_name or "User",
        email=normalized_email,
        password_hash=get_password_hash(payload.password),
        role=role_to_assign,
    )

    # Add employee within a transaction, supporting both sync and async sessions
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession3
    if isinstance(db, _AsyncSession3):
        db.add(employee)
        await db.flush()
        db.add(LeaveBalance(employee_id=employee.id, leaves_allowed=24, leaves_taken=0))
        db.add(Compensation(employee_id=employee.id, base_salary=100000.0 if role_to_assign == EmployeeRole.COMPANY_ADMIN else 50000.0, payment_date=28))
        await db.refresh(employee)
        await db.commit()
    else:
        db.add(employee)
        db.flush()
        db.add(LeaveBalance(employee_id=employee.id, leaves_allowed=24, leaves_taken=0))
        db.add(Compensation(employee_id=employee.id, base_salary=100000.0 if role_to_assign == EmployeeRole.COMPANY_ADMIN else 50000.0, payment_date=28))
        db.refresh(employee)
        db.commit()

    token = create_access_token(subject=employee.email, role=employee.role.value, company_id=employee.company_id, extra={"employee_id": str(employee.id)})
    user_out = UserOut(
        id=employee.id,
        email=employee.email,
        first_name=employee.first_name,
        last_name=employee.last_name,
        role=employee.role.value
    )
    return APIResponse(
        message="Employee created and logged in",
        data=TokenData(access_token=token, token_type="bearer", user=user_out),
    )


@router.post(
    "/company/register",
    response_model=APIResponse[TokenData],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Company & Admin account"
)
async def register_company(payload: CompanyRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Creates a new Company, its primary COMPANY_ADMIN employee, default leave balance, and compensation."""
    # Check domain uniqueness
    stmt_c = select(Company).where(Company.domain == payload.domain)
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession_f
    if isinstance(db, _AsyncSession_f):
        res_c = await db.execute(stmt_c)
    else:
        res_c = db.execute(stmt_c)
    exists_c = res_c.scalar_one_or_none()
    if exists_c:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company domain already registered")

    # Check email uniqueness globally
    stmt_e = select(Employee).where(Employee.email == payload.admin_email)
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession_g
    if isinstance(db, _AsyncSession_g):
        res_e = await db.execute(stmt_e)
    else:
        res_e = db.execute(stmt_e)
    exists_e = res_e.scalar_one_or_none()
    if exists_e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admin email already in use")

    try:
        # 1. Create Company
        company = Company(
            company_name=payload.company_name,
            domain=payload.domain,
            subscription_status=SubscriptionStatus.ACTIVE
        )
        db.add(company)
        await db.flush()

        # 2. Create Employee
        employee = Employee(
            company_id=company.id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.admin_email,
            password_hash=get_password_hash(payload.admin_password),
            role=EmployeeRole.COMPANY_ADMIN
        )
        db.add(employee)
        await db.flush()

        # 3. Create Leave Balance
        leave_balance = LeaveBalance(
            employee_id=employee.id,
            leaves_allowed=24,
            leaves_taken=0
        )
        db.add(leave_balance)

        # 4. Create Compensation
        compensation = Compensation(
            employee_id=employee.id,
            base_salary=100000.0,
            payment_date=28
        )
        db.add(compensation)

        await db.refresh(employee)
        await db.commit()

        token = create_access_token(subject=employee.email, role=employee.role.value, company_id=employee.company_id, extra={"employee_id": str(employee.id)})
        user_out = UserOut(
            id=employee.id,
            email=employee.email,
            first_name=employee.first_name,
            last_name=employee.last_name,
            role=employee.role.value
        )
        return APIResponse(
            message="Company registered and admin logged in",
            data=TokenData(access_token=token, token_type="bearer", user=user_out)
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {str(exc)}")

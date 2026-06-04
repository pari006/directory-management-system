import inspect
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.database_models import Employee, SuperAdmin, EmployeeRole, Company, SubscriptionStatus
from app.core.exceptions import TenantIsolationError, EmployeeNotFound

security = HTTPBearer()


async def _execute(session: AsyncSession, statement, params: dict | None = None):
    result = session.execute(statement, params) if params is not None else session.execute(statement)
    if inspect.isawaitable(result):
        return await result
    return result


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            try:
                if _is_postgres_session(session):
                    await session.execute(text("SELECT set_config('app.current_company_id', '', false)"))
                    await session.commit()
            except Exception:
                pass


class TokenPayload:
    def __init__(self, sub: str, role: str, company_id: Optional[str] = None, employee_id: Optional[str] = None):
        self.sub = sub
        self.role = role
        self.company_id = UUID(company_id) if company_id else None
        self.employee_id = UUID(employee_id) if employee_id else None


def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        role = payload.get("role")
        company_id = payload.get("company_id")
        employee_id = payload.get("employee_id")

        if not email or not role:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        return TokenPayload(sub=email, role=role, company_id=company_id, employee_id=employee_id)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


async def _get_employee_by_email(session: AsyncSession, email: str, company_id: Optional[UUID] = None) -> Optional[Employee]:
    if company_id:
        stmt = select(Employee).where(Employee.email == email, Employee.company_id == company_id)
    else:
        stmt = select(Employee).where(Employee.email == email)
    result = await _execute(session, stmt)
    return result.scalar_one_or_none()


async def _get_superadmin_by_email(session: AsyncSession, email: str) -> Optional[SuperAdmin]:
    stmt = select(SuperAdmin).where(SuperAdmin.email == email)
    result = await _execute(session, stmt)
    return result.scalar_one_or_none()


async def _ensure_company_active(session: AsyncSession, company_id: UUID):
    stmt = select(Company).where(Company.id == company_id)
    res = await _execute(session, stmt)
    company = res.scalar_one_or_none()
    if company and company.subscription_status == SubscriptionStatus.SUSPENDED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company subscription suspended; access locked")


def _is_postgres_session(session: AsyncSession) -> bool:
    bind = session.get_bind()
    dialect = getattr(bind, "dialect", None)
    return getattr(dialect, "name", "") == "postgresql"


async def _set_current_company(session: AsyncSession, company_id: UUID | None):
    if not _is_postgres_session(session):
        return

    value = str(company_id) if company_id else ""
    await _execute(
        session,
        text("SELECT set_config('app.current_company_id', :val, false)"),
        {"val": value},
    )


async def get_current_user(
    token: TokenPayload = Depends(get_current_token),
    db: AsyncSession = Depends(get_db),
) -> Employee:
    if token.company_id:
        await _set_current_company(db, token.company_id)

    # Prefer explicit employee_id if provided
    if token.employee_id:
        stmt = select(Employee).where(Employee.id == token.employee_id)
        res = await _execute(db, stmt)
        user = res.scalar_one_or_none()
    else:
        # If company_id provided, scope the email lookup to company to avoid duplicates
        user = await _get_employee_by_email(db, token.sub, company_id=token.company_id if token.company_id else None)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if user.role != EmployeeRole(token.role):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token role")

    if token.company_id and user.company_id != token.company_id:
        raise TenantIsolationError()

    await _ensure_company_active(db, user.company_id)
    return user


async def require_super_admin(
    token: TokenPayload = Depends(get_current_token),
    db: AsyncSession = Depends(get_db),
) -> SuperAdmin:
    if token.role != EmployeeRole.SUPER_ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin role required")

    if token.company_id is not None:
        raise TenantIsolationError("Super admin tokens cannot have company_id")

    await _set_current_company(db, None)

    admin = await _get_superadmin_by_email(db, token.sub)
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Super admin not found")
    return admin


async def require_company_admin(
    token: TokenPayload = Depends(get_current_token),
    db: AsyncSession = Depends(get_db),
) -> Employee:
    if token.role not in [EmployeeRole.COMPANY_ADMIN.value, EmployeeRole.SUPER_ADMIN.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company admin role required")

    if not token.company_id:
        raise TenantIsolationError("Company admin token must have company_id")

    await _set_current_company(db, token.company_id)

    # Prefer explicit employee_id if provided in token (disambiguates duplicate emails)
    if token.employee_id:
        stmt = select(Employee).where(Employee.id == token.employee_id, Employee.company_id == token.company_id)
        res = await _execute(db, stmt)
        user = res.scalar_one_or_none()
    else:
        stmt = select(Employee).where(Employee.email == token.sub, Employee.company_id == token.company_id)
        res = await _execute(db, stmt)
        # Use first matching result to avoid MultipleResultsFound when duplicates exist
        user = res.scalars().first()

    if not user:
        raise EmployeeNotFound()

    await _ensure_company_active(db, user.company_id)
    return user


async def require_employee(
    token: TokenPayload = Depends(get_current_token),
    db: AsyncSession = Depends(get_db),
) -> Employee:
    if not token.company_id:
        raise TenantIsolationError("Employee token must have company_id")

    await _set_current_company(db, token.company_id)

    # Prefer explicit employee_id if provided in token (disambiguates duplicate emails)
    if token.employee_id:
        stmt = select(Employee).where(Employee.id == token.employee_id, Employee.company_id == token.company_id)
        res = await _execute(db, stmt)
        user = res.scalar_one_or_none()
    else:
        stmt = select(Employee).where(Employee.email == token.sub, Employee.company_id == token.company_id)
        res = await _execute(db, stmt)
        # Use first matching result to avoid MultipleResultsFound when duplicates exist
        user = res.scalars().first()

    if not user:
        raise EmployeeNotFound()

    await _ensure_company_active(db, user.company_id)
    return user


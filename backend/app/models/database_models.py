from __future__ import annotations

from datetime import datetime, date
from enum import Enum as PyEnum
from uuid import UUID, uuid4
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, Date, Enum, Index, String, UniqueConstraint, Uuid, func, ForeignKey, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from sqlalchemy.orm import RelationshipProperty


# ==========================================
# CORE PLATFORM ENUMS
# ==========================================

class UserRole(str, PyEnum):
    ADMIN = "ADMIN"
    USER = "USER"


class EmployeeRole(str, PyEnum):
    SUPER_ADMIN = "SUPER_ADMIN"
    COMPANY_ADMIN = "COMPANY_ADMIN"
    EMPLOYEE = "EMPLOYEE"


class SubscriptionStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class LeaveRequestStatus(str, PyEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class BillingStatus(str, PyEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"


# ==========================================
# ADMINISTRATIVE DOMAIN MODELS
# ==========================================

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        default=UserRole.USER,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SuperAdmin(Base):
    __tablename__ = "super_admins"
    __table_args__ = (
        UniqueConstraint("email", name="uq_super_admins_email"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ==========================================
# LEAF ENTITY/METADATA SUB-TABLES
# ==========================================

class Compensation(Base):
    __tablename__ = "compensation"
    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_compensation_employee_id"),
        Index("ix_compensation_employee_id", "employee_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    base_salary: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    payment_date: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    employee: Mapped[Employee] = relationship("Employee", back_populates="compensation")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_leave_balances_employee_id"),
        Index("ix_leave_balances_employee_id", "employee_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    leaves_allowed: Mapped[int] = mapped_column(Integer, nullable=False)
    leaves_taken: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    employee: Mapped[Employee] = relationship("Employee", back_populates="leave_balance")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    __table_args__ = (
        Index("ix_leave_requests_employee_id", "employee_id"),
        Index("ix_leave_requests_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[LeaveRequestStatus] = mapped_column(
        Enum(LeaveRequestStatus, name="leave_request_status", native_enum=True),
        default=LeaveRequestStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    employee: Mapped[Employee] = relationship("Employee", back_populates="leave_requests")


# ==========================================
# TENANT IDENTITY & EMPLOYEES CORE INTERSECTION
# ==========================================

class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        Index("ix_employees_company_id", "company_id"),
        Index("ix_employees_email", "email"),
    )


    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[EmployeeRole] = mapped_column(
        Enum(EmployeeRole, name="employee_role", native_enum=True),
        default=EmployeeRole.EMPLOYEE,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    company: Mapped[Company] = relationship("Company", back_populates="employees")
    compensation: Mapped[Compensation | None] = relationship("Compensation", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    leave_balance: Mapped[LeaveBalance | None] = relationship("LeaveBalance", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    leave_requests: Mapped[list[LeaveRequest]] = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan")

    @property
    def base_salary(self) -> float | None:
        return float(self.compensation.base_salary) if self.compensation else None

    @property
    def payment_date(self) -> int | None:
        return self.compensation.payment_date if self.compensation else None

    @property
    def leaves_allowed(self) -> int | None:
        return self.leave_balance.leaves_allowed if self.leave_balance else None

    @property
    def leaves_taken(self) -> int | None:
        return self.leave_balance.leaves_taken if self.leave_balance else None


class BillingLedger(Base):
    __tablename__ = "billing_ledger"
    __table_args__ = (
        Index("ix_billing_ledger_company_id", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    amount_simulated: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[BillingStatus] = mapped_column(
        Enum(BillingStatus, name="billing_status", native_enum=True),
        default=BillingStatus.PENDING,
        nullable=False,
    )
    billing_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    company: Mapped[Company] = relationship("Company", back_populates="billing_ledger")


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("domain", name="uq_companies_domain"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status", native_enum=True),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    employees: Mapped[list[Employee]] = relationship("Employee", back_populates="company", cascade="all, delete-orphan")
    billing_ledger: Mapped[list[BillingLedger]] = relationship("BillingLedger", back_populates="company", cascade="all, delete-orphan")
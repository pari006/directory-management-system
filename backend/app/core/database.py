from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings


# Async engine for application
async_engine = create_async_engine(settings.database_url, future=True)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)
Base = declarative_base()


async def init_rls_policies(conn):
    """Initialize PostgreSQL Row-Level Security policies for multi-tenancy.

    The application now runs on PostgreSQL only, so the policies are applied
    directly against the live async connection created during startup.
    """
    if "postgresql" not in settings.database_url:
        return

    # Remove legacy unique constraint on (company_id, email) to allow duplicate emails
    await conn.execute(text("ALTER TABLE employees DROP CONSTRAINT IF EXISTS uq_employees_company_email"))

    await conn.execute(text("ALTER TABLE employees ENABLE ROW LEVEL SECURITY"))
    await conn.execute(text("ALTER TABLE compensation ENABLE ROW LEVEL SECURITY"))
    await conn.execute(text("ALTER TABLE leave_balances ENABLE ROW LEVEL SECURITY"))
    await conn.execute(text("ALTER TABLE leave_requests ENABLE ROW LEVEL SECURITY"))
    await conn.execute(text("ALTER TABLE billing_ledger ENABLE ROW LEVEL SECURITY"))

    await conn.execute(text("DROP POLICY IF EXISTS tenant_isolation_employees ON employees"))
    await conn.execute(text("""
        CREATE POLICY tenant_isolation_employees ON employees FOR ALL
        USING (company_id = COALESCE(current_setting('app.current_company_id')::uuid, company_id))
    """))

    await conn.execute(text("DROP POLICY IF EXISTS tenant_isolation_compensation ON compensation"))
    await conn.execute(text("""
        CREATE POLICY tenant_isolation_compensation ON compensation FOR ALL
        USING (employee_id IN (
            SELECT id FROM employees
            WHERE company_id = COALESCE(current_setting('app.current_company_id')::uuid, company_id)
        ))
    """))

    await conn.execute(text("DROP POLICY IF EXISTS tenant_isolation_leave_balances ON leave_balances"))
    await conn.execute(text("""
        CREATE POLICY tenant_isolation_leave_balances ON leave_balances FOR ALL
        USING (employee_id IN (
            SELECT id FROM employees
            WHERE company_id = COALESCE(current_setting('app.current_company_id')::uuid, company_id)
        ))
    """))

    await conn.execute(text("DROP POLICY IF EXISTS tenant_isolation_leave_requests ON leave_requests"))
    await conn.execute(text("""
        CREATE POLICY tenant_isolation_leave_requests ON leave_requests FOR ALL
        USING (employee_id IN (
            SELECT id FROM employees
            WHERE company_id = COALESCE(current_setting('app.current_company_id')::uuid, company_id)
        ))
    """))

    await conn.execute(text("DROP POLICY IF EXISTS tenant_isolation_billing_ledger ON billing_ledger"))
    await conn.execute(text("""
        CREATE POLICY tenant_isolation_billing_ledger ON billing_ledger FOR ALL
        USING (company_id = COALESCE(current_setting('app.current_company_id')::uuid, company_id))
    """))

import asyncio
from pathlib import Path
import sys

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.api.deps import get_db
from app.core.database import Base
from app.core.security import get_password_hash
from app.main import app
from app.models.database_models import SuperAdmin


engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def reset_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        session.add(
            SuperAdmin(
                email="superadmin@orchard.example.com",
                password_hash=get_password_hash("Password123"),
            )
        )
        await session.commit()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    asyncio.run(reset_database())


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_company_admin(email: str = "admin@example.com") -> tuple[dict, dict[str, str]]:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123",
            "first_name": "Company",
            "last_name": "Admin",
            "role": "ADMIN",
        },
    )
    assert response.status_code == 201, response.text
    token_data = response.json()["data"]
    return token_data, auth_headers(token_data["access_token"])


def admin_company_id(headers: dict[str, str]) -> str:
    response = client.get("/api/v1/employees", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["data"]["items"][0]["company_id"]


def register_employee(company_id: str, email: str = "employee@example.com") -> tuple[dict, dict[str, str]]:
    response = client.post(
        f"/api/v1/auth/signup?company_id={company_id}",
        json={
            "email": email,
            "password": "Password123",
            "first_name": "Team",
            "last_name": "Member",
            "role": "USER",
        },
    )
    assert response.status_code == 201, response.text
    token_data = response.json()["data"]
    return token_data, auth_headers(token_data["access_token"])


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_company_admin_auth_and_employee_crud():
    _, headers = register_company_admin()

    created = client.post(
        "/api/v1/employees",
        headers=headers,
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "role": "EMPLOYEE",
            "base_salary": 92000,
            "payment_date": 25,
            "leaves_allowed": 20,
        },
    )
    assert created.status_code == 201, created.text
    employee = created.json()["data"]
    assert employee["base_salary"] == 92000
    assert employee["payment_date"] == 25
    assert employee["leaves_allowed"] == 20

    listed = client.get("/api/v1/employees?search=Jane&sort_by=first_name&sort_order=asc", headers=headers)
    assert listed.status_code == 200, listed.text
    assert listed.json()["data"]["total"] == 1

    detail = client.get(f"/api/v1/employees/{employee['id']}", headers=headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"]["email"] == "jane@example.com"

    updated = client.put(
        f"/api/v1/employees/{employee['id']}",
        headers=headers,
        json={"base_salary": 98000, "payment_date": 28, "leaves_allowed": 24},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["base_salary"] == 98000
    assert updated.json()["data"]["leaves_allowed"] == 24

    deleted = client.delete(f"/api/v1/employees/{employee['id']}", headers=headers)
    assert deleted.status_code == 200, deleted.text

    missing = client.get(f"/api/v1/employees/{employee['id']}", headers=headers)
    assert missing.status_code == 404


def test_employee_permissions_and_leave_workflow():
    _, admin_headers = register_company_admin()
    company_id = admin_company_id(admin_headers)
    employee_token, employee_headers = register_employee(company_id)
    employee_id = employee_token["user"]["id"]

    denied = client.post(
        "/api/v1/employees",
        headers=employee_headers,
        json={
            "first_name": "Blocked",
            "last_name": "User",
            "email": "blocked@example.com",
            "role": "EMPLOYEE",
        },
    )
    assert denied.status_code == 403

    invalid_leave = client.post(
        "/api/v1/leaves/request",
        headers=employee_headers,
        json={"start_date": "2026-06-20", "end_date": "2026-06-19", "reason": "Invalid"},
    )
    assert invalid_leave.status_code == 400

    leave = client.post(
        "/api/v1/leaves/request",
        headers=employee_headers,
        json={"start_date": "2026-06-20", "end_date": "2026-06-22", "reason": "Vacation"},
    )
    assert leave.status_code == 201, leave.text
    leave_id = leave.json()["id"]

    mine = client.get("/api/v1/leaves/my-requests", headers=employee_headers)
    assert mine.status_code == 200, mine.text
    assert len(mine.json()) == 1

    company_queue = client.get("/api/v1/leaves/company", headers=admin_headers)
    assert company_queue.status_code == 200, company_queue.text
    assert company_queue.json()[0]["employee_email"] == "employee@example.com"

    approved = client.patch(
        f"/api/v1/leaves/{leave_id}/approve",
        headers=admin_headers,
        json={"status": "APPROVED"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "APPROVED"

    balance = client.get(f"/api/v1/leaves/{employee_id}/balance", headers=employee_headers)
    assert balance.status_code == 200, balance.text
    assert balance.json()["leaves_taken"] == 3
    assert balance.json()["available_balance"] == 21


def test_payroll_billing_and_platform_admin_controls():
    _, admin_headers = register_company_admin("billing-admin@example.com")

    payroll = client.get("/api/v1/admin/payroll/summary", headers=admin_headers)
    assert payroll.status_code == 200, payroll.text
    assert payroll.json()["headcount"] == 1
    assert payroll.json()["total_payroll_overhead"] == 100000

    payment = client.post(
        "/api/v1/billing/company/simulate?amount=2500&status=PAID",
        headers=admin_headers,
    )
    assert payment.status_code == 200, payment.text

    company_ledger = client.get("/api/v1/billing/company/ledger", headers=admin_headers)
    assert company_ledger.status_code == 200, company_ledger.text
    assert company_ledger.json()[0]["amount"] == 2500

    super_login = client.post(
        "/api/v1/auth/superadmin/login",
        json={"email": "superadmin@orchard.example.com", "password": "Password123"},
    )
    assert super_login.status_code == 200, super_login.text
    super_headers = auth_headers(super_login.json()["data"]["access_token"])

    companies = client.get("/api/v1/superadmin/companies", headers=super_headers)
    assert companies.status_code == 200, companies.text
    company_id = companies.json()[0]["id"]

    simulated = client.post(
        f"/api/v1/billing/simulate?company_id={company_id}&amount=1500&status=PENDING",
        headers=super_headers,
    )
    assert simulated.status_code == 200, simulated.text

    platform_ledger = client.get("/api/v1/billing/ledger", headers=super_headers)
    assert platform_ledger.status_code == 200, platform_ledger.text
    assert len(platform_ledger.json()) == 2

    toggled = client.post(f"/api/v1/superadmin/companies/{company_id}/toggle-status", headers=super_headers)
    assert toggled.status_code == 200, toggled.text
    assert toggled.json()["subscription_status"] == "SUSPENDED"

    blocked_login = client.post(
        "/api/v1/auth/login",
        json={"email": "billing-admin@example.com", "password": "Password123"},
    )
    assert blocked_login.status_code == 403

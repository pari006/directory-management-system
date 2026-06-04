import os
import sys
import uuid
from datetime import date, timedelta

import psycopg

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.security import get_password_hash


SEED_PASSWORD_ENV = "SEED_PASSWORD"
SEED_DATABASE_URL_ENV = "SEED_DATABASE_URL"
DEFAULT_SEED_DATABASE_URL = "dbname=employee_directory user=postgres host=localhost"


EMPLOYEES = [
    ("Aarav", "Mehta", "aarav.mehta@abc.com", "COMPANY_ADMIN", 165000, 28, 28, 2),
    ("Maya", "Sharma", "maya.sharma@abc.com", "EMPLOYEE", 92000, 28, 24, 4),
    ("Rohan", "Kapoor", "rohan.kapoor@abc.com", "EMPLOYEE", 88000, 28, 24, 1),
    ("Isha", "Nair", "isha.nair@abc.com", "EMPLOYEE", 78000, 25, 22, 6),
    ("Kabir", "Singh", "kabir.singh@abc.com", "EMPLOYEE", 110000, 28, 24, 3),
    ("Ananya", "Rao", "ananya.rao@abc.com", "EMPLOYEE", 83000, 30, 24, 0),
    ("Neel", "Verma", "neel.verma@abc.com", "EMPLOYEE", 72000, 28, 20, 5),
    ("Sara", "Khan", "sara.khan@abc.com", "EMPLOYEE", 97000, 28, 24, 2),
]


def seed():
    seed_password = os.getenv(SEED_PASSWORD_ENV)
    if not seed_password:
        raise RuntimeError(f"Set {SEED_PASSWORD_ENV} before running the seed script.")

    conn_string = os.getenv(SEED_DATABASE_URL_ENV, DEFAULT_SEED_DATABASE_URL)
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            print("Connected to PostgreSQL. Deleting previous application data...")
            cur.execute(
                """
                TRUNCATE TABLE
                    billing_ledger,
                    leave_requests,
                    leave_balances,
                    compensation,
                    employees,
                    companies,
                    super_admins,
                    users
                RESTART IDENTITY CASCADE
                """
            )

            company_id = uuid.uuid4()
            cur.execute(
                """
                INSERT INTO companies (id, company_name, domain, subscription_status, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (company_id, "abc", "abc.com", "ACTIVE"),
            )

            employee_ids = {}
            password_hash = get_password_hash(seed_password)
            for first_name, last_name, email, role, salary, payment_date, leaves_allowed, leaves_taken in EMPLOYEES:
                employee_id = uuid.uuid4()
                employee_ids[email] = employee_id
                cur.execute(
                    """
                    INSERT INTO employees
                        (id, company_id, first_name, last_name, email, role, password_hash, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (employee_id, company_id, first_name, last_name, email, role, password_hash),
                )
                cur.execute(
                    """
                    INSERT INTO leave_balances
                        (id, employee_id, leaves_allowed, leaves_taken, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    """,
                    (uuid.uuid4(), employee_id, leaves_allowed, leaves_taken),
                )
                cur.execute(
                    """
                    INSERT INTO compensation
                        (id, employee_id, base_salary, payment_date, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    """,
                    (uuid.uuid4(), employee_id, salary, payment_date),
                )

            today = date.today()
            leave_rows = [
                ("maya.sharma@abc.com", today + timedelta(days=5), today + timedelta(days=7), "Family function", "PENDING"),
                ("rohan.kapoor@abc.com", today - timedelta(days=12), today - timedelta(days=10), "Medical appointment", "APPROVED"),
                ("isha.nair@abc.com", today + timedelta(days=14), today + timedelta(days=15), "Personal work", "REJECTED"),
                ("kabir.singh@abc.com", today + timedelta(days=20), today + timedelta(days=24), "Vacation", "PENDING"),
            ]
            for email, start_date, end_date, reason, status in leave_rows:
                cur.execute(
                    """
                    INSERT INTO leave_requests
                        (id, employee_id, start_date, end_date, reason, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (uuid.uuid4(), employee_ids[email], start_date, end_date, reason, status),
                )

            ledger_rows = [
                (sum(employee[4] for employee in EMPLOYEES) / 12, "PAID"),
                (24500, "PENDING"),
                (18000, "FAILED"),
            ]
            for amount, status in ledger_rows:
                cur.execute(
                    """
                    INSERT INTO billing_ledger
                        (id, company_id, amount_simulated, status, billing_date)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (uuid.uuid4(), company_id, amount, status),
                )

            cur.execute(
                """
                INSERT INTO super_admins (id, email, password_hash, created_at)
                VALUES (%s, %s, %s, NOW())
                """,
                (uuid.uuid4(), "superadmin@orchard.com", get_password_hash(seed_password)),
            )

        conn.commit()

    print("Database reset complete.")
    print(f"Company: abc ({company_id})")
    print("Company admin login: aarav.mehta@abc.com / <SEED_PASSWORD>")
    print("Employee login: maya.sharma@abc.com / <SEED_PASSWORD>")
    print("Super admin login: superadmin@orchard.com / <SEED_PASSWORD>")


if __name__ == "__main__":
    seed()

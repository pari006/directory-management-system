# Architecture

## Overview

The Directory Management System is a React and FastAPI application for multi-tenant company workspaces. It separates the browser UI, API route layer, authentication and tenant enforcement dependencies, async SQLAlchemy persistence, and PostgreSQL row-level security setup.

## Frontend

The frontend lives in `frontend/src`.

- `App.jsx` contains the landing page, authentication modal, role-aware dashboard, directory, leave, payroll, billing, and platform admin screens.
- `api.js` centralizes API requests, error formatting, fallback API bases, and conversion between UI form fields and backend employee payloads.
- `styles.css` contains the application styling.

The app is built with Vite. Production output is generated into `frontend/dist/` and is ignored by Git because it is reproducible.

## Backend

The backend entry point is `backend/app/main.py`.

- FastAPI app creation and CORS middleware are configured there.
- Routers are mounted under both `/api` and `/api/v1`.
- Startup creates SQLAlchemy tables and applies PostgreSQL RLS policies through `init_rls_policies`.

Route modules:

- `auth.py`: company signup, company registration, unified login, company login, super admin login
- `employees.py`: company-scoped employee CRUD, search, sorting, and pagination
- `leaves.py`: leave request creation, approval, company queue, personal queue, leave balance
- `payroll.py`: company payroll summary
- `billing.py`: company and platform billing ledger simulation
- `superadmin.py`: platform company list and company suspension toggle

## Data Model

The canonical models are in `backend/app/models/database_models.py`.

Core tables:

- `companies`
- `employees`
- `super_admins`
- `compensation`
- `leave_balances`
- `leave_requests`
- `billing_ledger`

Employees are tenant-scoped through `company_id`. Compensation and leave records are linked to employees. Billing ledger rows are linked to companies.

## Authentication and Tenant Isolation

Passwords are hashed with Argon2 in `backend/app/core/security.py`. Legacy bcrypt verification is kept for older hashes.

JWTs include:

- `sub`
- `role`
- `company_id` for tenant users
- `employee_id` for company users
- `exp`

`backend/app/api/deps.py` validates tokens, loads the current user, enforces role requirements, checks company suspension status, and sets PostgreSQL `app.current_company_id` for RLS-aware requests.

## Database Runtime

Normal runtime uses PostgreSQL through `postgresql+asyncpg`. The app uses SQLAlchemy async sessions and commits successful requests in `get_db`; failures are rolled back.

The automated tests use `sqlite+aiosqlite` with an in-memory database so API flows can be validated without a live PostgreSQL service. PostgreSQL-specific RLS setup is skipped unless the configured database URL contains PostgreSQL.

## Verification Boundary

`backend/tests/test_api.py` is an integration-style suite using FastAPI `TestClient`. It covers auth, employees, leave, payroll, billing, and super admin flows against the current API contracts. The frontend verification currently uses `npm run build`.

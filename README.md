<div align="center">

<h1>
  <span style="color:#14b8a6;">Orchard</span>
  <span style="color:#64748b;">Directory Management System</span>
</h1>

<p>
  <strong>A polished multi-tenant workforce platform for directories, leave, payroll, billing, and platform administration.</strong>
</p>

<p>
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0f766e?style=for-the-badge&logo=fastapi&logoColor=white">
  <img alt="React" src="https://img.shields.io/badge/React-2563eb?style=for-the-badge&logo=react&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-334155?style=for-the-badge&logo=postgresql&logoColor=white">
  <img alt="Vite" src="https://img.shields.io/badge/Vite-f59e0b?style=for-the-badge&logo=vite&logoColor=white">
</p>

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-111827?style=flat-square&logo=python&logoColor=white">
  <img alt="Tests" src="https://img.shields.io/badge/API_tests-passing-16a34a?style=flat-square">
  <img alt="Security" src="https://img.shields.io/badge/secrets-ignored-7c3aed?style=flat-square">
  <img alt="Status" src="https://img.shields.io/badge/status-GitHub_ready-0ea5e9?style=flat-square">
</p>

</div>

<div align="center">

```text
Company Workspaces  ->  Employee Directory  ->  Leave + Payroll  ->  Billing Ledger  ->  Platform Control
```

</div>

## Overview

Orchard is an elegant, full-stack workforce management platform built for modern company operations. It brings employee directories, role-based access, leave workflows, payroll visibility, simulated billing, and platform administration into one clean multi-tenant application.

The project is designed as a production-minded academic/demo system: secure authentication, tenant-aware data access, a polished React interface, automated API coverage, and GitHub-ready repository hygiene.

## Highlights

| Capability | What it delivers |
| --- | --- |
| Tenant workspaces | Isolated company data with role-aware access boundaries |
| Secure auth | JWT access tokens, Argon2 password hashing, legacy bcrypt verification |
| Employee directory | CRUD, search, sorting, pagination, profile details |
| Leave operations | Employee requests, admin approval/rejection, balance tracking |
| Payroll visibility | Headcount, salary overhead, payment schedule data |
| Billing simulation | Company and platform ledger workflows |
| Platform admin | Company listing, billing overview, suspension controls |
| Verification | Integration tests across auth, employees, leave, payroll, billing, and superadmin |

## Tech Stack

| Layer | Tools |
| --- | --- |
| Frontend | React 18, Vite, CSS |
| Backend | FastAPI, SQLAlchemy async sessions, Pydantic |
| Database | PostgreSQL for runtime, async SQLite for tests |
| Auth | JWT, Argon2, legacy bcrypt verification support |
| Testing | Pytest, FastAPI TestClient |

## Core Modules

```text
backend/
  app/
    api/deps.py              # auth, role checks, tenant enforcement, db session lifecycle
    api/routes/              # auth, employees, leaves, payroll, billing, superadmin
    core/                    # settings, database, security, exception handlers
    models/database_models.py # canonical SQLAlchemy data model
    schemas/                 # request and response schemas
  tests/test_api.py          # integration coverage for API workflows
  requirements.txt
  seed.py

frontend/
  src/App.jsx                # landing page, dashboard, directory, leave, payroll, platform UI
  src/api.js                 # API client and payload normalization
  src/styles.css             # application styling
  package.json
```

## Product Surface

**Company users**

- Create a company workspace
- Sign in with email and password
- View role-aware dashboards
- Browse and search the employee directory
- Submit and track leave requests

**Company admins**

- Manage employees
- Approve or reject leave requests
- Review leave balances
- View payroll summaries
- Record simulated payment runs

**Super admins**

- View all tenant companies
- Review platform billing ledgers
- Simulate platform billing entries
- Suspend or reactivate company access

## Quick Start

Clone the repository and create a local environment file:

```powershell
Copy-Item .env.example .env
```

Update `.env` with your PostgreSQL connection string and a strong `SECRET_KEY`.

### Backend

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API docs:

```text
http://127.0.0.1:8000/docs
```

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The app will be available at:

```text
http://127.0.0.1:5173
```

## Optional Demo Data

The seed script intentionally does not hardcode passwords. Set the seed password yourself before running it:

```powershell
cd backend
$env:SEED_PASSWORD = "choose-a-demo-password"
$env:SEED_DATABASE_URL = "dbname=employee_directory user=postgres host=localhost"
python seed.py
```

Seeded users:

- Company admin: `aarav.mehta@abc.com`
- Employee: `maya.sharma@abc.com`
- Super admin: `superadmin@orchard.com`

All seeded users use the password from `SEED_PASSWORD`.

## Verification

Run backend tests:

```powershell
cd backend
python -m pytest -q
```

Run a Python syntax check without writing bytecode:

```powershell
python -B -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for root in ('app','tests') for p in pathlib.Path(root).rglob('*.py')]; print('syntax ok')"
```

Build the frontend:

```powershell
cd ..\frontend
npm run build
```

## Security and Repository Hygiene

This repository is prepared for public GitHub hosting:

- `.env` is ignored
- local database files are ignored
- logs, caches, virtual environments, `node_modules`, and build output are ignored
- `.env.example` contains placeholders only
- seed credentials are environment-driven

Do not commit real production secrets, database passwords, private keys, or generated deployment artifacts.

## Documentation

- [API Documentation](API_DOCUMENTATION.md)
- [Architecture](ARCHITECTURE.md)
- [Setup Guide](SETUP_GUIDE.md)
- [Verification Checklist](VERIFICATION_CHECKLIST.md)

## Status

The project has been cleaned, tested, and prepared for GitHub. It is ready for continued development, deployment planning, and feature expansion.

<div align="center">

# 🌳 Orchard
### Directory Management System

**A polished multi-tenant workforce platform for directories, leave, payroll, billing, and platform administration.**

<br/>

![FastAPI](https://img.shields.io/badge/FastAPI-0f766e?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-2563eb?style=for-the-badge&logo=react&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-334155?style=for-the-badge&logo=postgresql&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-f59e0b?style=for-the-badge&logo=vite&logoColor=white)

![Python](https://img.shields.io/badge/Python-3.11+-111827?style=flat-square&logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/API_tests-passing-16a34a?style=flat-square)
![Security](https://img.shields.io/badge/secrets-ignored-7c3aed?style=flat-square)
![Status](https://img.shields.io/badge/status-GitHub_ready-0ea5e9?style=flat-square)

<br/>

**[Overview](#-overview)** · **[Highlights](#-highlights)** · **[Quick Start](#-quick-start)** · **[Modules](#%EF%B8%8F-core-modules)** · **[Docs](#-documentation)**

<br/>

```text
Company Workspaces  →  Employee Directory  →  Leave + Payroll  →  Billing Ledger  →  Platform Control
```

</div>

<br/>

## 🏢 Overview

Orchard is an elegant, full-stack **workforce management platform** built for modern company operations. It brings employee directories, role-based access, leave workflows, payroll visibility, simulated billing, and platform administration into one clean multi-tenant application.

The project is designed as a **production-minded academic/demo system**: secure authentication, tenant-aware data access, a polished React interface, automated API coverage, and GitHub-ready repository hygiene.

<br/>

## ✨ Highlights

<table>
<tr>
<td width="50%" valign="top">

### 🏬 Multi-Tenancy & Access
- Isolated company workspaces with role-aware boundaries
- JWT access tokens
- Argon2 password hashing with legacy bcrypt verification

### 👥 Employee Directory
- Full CRUD
- Search, sorting, pagination
- Rich profile details

</td>
<td width="50%" valign="top">

### 🗓️ Leave & Payroll
- Employee leave requests
- Admin approval / rejection flows
- Balance tracking
- Headcount, salary overhead & payment schedules

### 💳 Billing & Platform Control
- Company + platform billing simulation
- Company listing, suspension controls

</td>
</tr>
</table>

<div align="center">

| Capability | What it delivers |
| :--- | :--- |
| 🏢 Tenant workspaces | Isolated company data with role-aware access boundaries |
| 🔐 Secure auth | JWT access tokens, Argon2 password hashing, legacy bcrypt verification |
| 👥 Employee directory | CRUD, search, sorting, pagination, profile details |
| 🗓️ Leave operations | Employee requests, admin approval/rejection, balance tracking |
| 💰 Payroll visibility | Headcount, salary overhead, payment schedule data |
| 🧾 Billing simulation | Company and platform ledger workflows |
| 🛠️ Platform admin | Company listing, billing overview, suspension controls |
| ✅ Verification | Integration tests across auth, employees, leave, payroll, billing, and superadmin |

</div>

<br/>

## 🛠️ Tech Stack

| Layer | Tools |
| :--- | :--- |
| **Frontend** | React 18 · Vite · CSS |
| **Backend** | FastAPI · SQLAlchemy async sessions · Pydantic |
| **Database** | PostgreSQL (runtime) · async SQLite (tests) |
| **Auth** | JWT · Argon2 · legacy bcrypt verification support |
| **Testing** | Pytest · FastAPI TestClient |

<br/>

## 🗂️ Core Modules

```text
backend/
  app/
    api/deps.py               # auth, role checks, tenant enforcement, db session lifecycle
    api/routes/                # auth, employees, leaves, payroll, billing, superadmin
    core/                      # settings, database, security, exception handlers
    models/database_models.py  # canonical SQLAlchemy data model
    schemas/                   # request and response schemas
  tests/test_api.py           # integration coverage for API workflows
  requirements.txt
  seed.py

frontend/
  src/App.jsx                 # landing page, dashboard, directory, leave, payroll, platform UI
  src/api.js                  # API client and payload normalization
  src/styles.css               # application styling
  package.json
```

<br/>

## 🧭 Product Surface

<table>
<tr>
<td width="33%" valign="top">

### 👤 Company Users
- Create a company workspace
- Sign in with email and password
- View role-aware dashboards
- Browse and search the employee directory
- Submit and track leave requests

</td>
<td width="33%" valign="top">

### 🛡️ Company Admins
- Manage employees
- Approve or reject leave requests
- Review leave balances
- View payroll summaries
- Record simulated payment runs

</td>
<td width="33%" valign="top">

### 👑 Super Admins
- View all tenant companies
- Review platform billing ledgers
- Simulate platform billing entries
- Suspend or reactivate company access

</td>
</tr>
</table>

<br/>

## 🚀 Quick Start

**1️⃣ Clone the repo & create a local environment file**

```powershell
Copy-Item .env.example .env
```

> Update `.env` with your PostgreSQL connection string and a strong `SECRET_KEY`.

**2️⃣ Start the backend**

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

**3️⃣ Start the frontend** *(new terminal)*

```powershell
cd frontend
npm install
npm run dev
```

The app will be available at:

```text
http://127.0.0.1:5173
```

<br/>

## 🌱 Optional Demo Data

The seed script intentionally does **not** hardcode passwords. Set the seed password yourself before running it:

```powershell
cd backend
$env:SEED_PASSWORD = "choose-a-demo-password"
$env:SEED_DATABASE_URL = "dbname=employee_directory user=postgres host=localhost"
python seed.py
```

<div align="center">

| Role | Seeded email |
| :--- | :--- |
| 🛡️ Company admin | `aarav.mehta@abc.com` |
| 👤 Employee | `maya.sharma@abc.com` |
| 👑 Super admin | `superadmin@orchard.com` |

*All seeded users use the password from `SEED_PASSWORD`.*

</div>

<br/>

## ✅ Verification

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

<br/>

## 🔒 Security & Repository Hygiene

This repository is prepared for public GitHub hosting:

- ✅ `.env` is ignored
- ✅ Local database files are ignored
- ✅ Logs, caches, virtual environments, `node_modules`, and build output are ignored
- ✅ `.env.example` contains placeholders only
- ✅ Seed credentials are environment-driven

> ⚠️ **Never commit** real production secrets, database passwords, private keys, or generated deployment artifacts.

<br/>

## 📚 Documentation

| Document | Description |
| :--- | :--- |
| 📘 [API Documentation](API_DOCUMENTATION.md) | Full API reference |
| 🏗️ [Architecture](ARCHITECTURE.md) | System design overview |
| ⚙️ [Setup Guide](SETUP_GUIDE.md) | Step-by-step environment setup |
| ✅ [Verification Checklist](VERIFICATION_CHECKLIST.md) | Pre-deployment checks |

<br/>

<div align="center">

---

### 📌 Status

**Cleaned. Tested. GitHub-ready.**
Ready for continued development, deployment planning, and feature expansion.

<br/>

*Built layer by layer — from tenant to table.* 🌳

</div>

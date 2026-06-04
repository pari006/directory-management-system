# Directory Management System

Full-stack directory management application for company workspaces. The current codebase supports company signup/login, employee directory CRUD, leave requests and approvals, payroll summaries, simulated billing ledgers, and platform-level super admin controls.

## Tech Stack

- Frontend: React 18 + Vite
- Backend: FastAPI + SQLAlchemy async sessions
- Database: PostgreSQL for normal runtime; async SQLite is used only by automated tests
- Auth: JWT access tokens with Argon2 password hashing and legacy bcrypt verification support

## Project Structure

```text
backend/
  app/
    api/deps.py              # auth dependencies, tenant checks, db session lifecycle
    api/routes/              # auth, employees, leaves, payroll, billing, superadmin
    core/                    # settings, database, security, exception handlers
    models/database_models.py
    schemas/
  tests/test_api.py          # API integration coverage
  requirements.txt
  seed.py
frontend/
  src/App.jsx
  src/api.js
  src/styles.css
  package.json
```

## Quick Start

1. Create `.env` from `.env.example` and update `DATABASE_URL`.
2. Install backend dependencies:

```powershell
cd backend
pip install -r requirements.txt
```

3. Start the backend:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

4. Install and start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

5. Open `http://127.0.0.1:5173`.

## Verification

```powershell
cd backend
python -m pytest -q

cd ..\frontend
npm run build
```

The repository is prepared for GitHub with `.gitignore` rules for `.env`, virtual environments, caches, logs, local database files, `node_modules`, and frontend build output.

# Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL running locally or remotely

## Backend

From the repository root:

```powershell
cd backend
pip install -r requirements.txt
```

Create a root `.env` file from `.env.example`:

```powershell
Copy-Item ..\.env.example ..\.env
```

Set `DATABASE_URL` to a PostgreSQL async URL, for example:

```env
DATABASE_URL=postgresql+asyncpg://postgres:<db-password>@127.0.0.1:5432/employee_directory
```

Start the API:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The app creates tables on startup through SQLAlchemy metadata and applies PostgreSQL RLS policies when the database URL is PostgreSQL.

Optional demo data:

```powershell
$env:SEED_PASSWORD = "choose-a-demo-password"
$env:SEED_DATABASE_URL = "dbname=employee_directory user=postgres host=localhost"
python seed.py
```

Seeded credentials:

- Company admin: `aarav.mehta@abc.com` / your `SEED_PASSWORD`
- Employee: `maya.sharma@abc.com` / your `SEED_PASSWORD`
- Super admin: `superadmin@orchard.com` / your `SEED_PASSWORD`

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend uses `VITE_API_BASE` when provided. Without it, `frontend/src/api.js` tries common local API bases including `http://127.0.0.1:8000/api/v1`.

## Production Build

```powershell
cd frontend
npm run build
```

The generated `frontend/dist/` directory is intentionally ignored for GitHub and can be rebuilt at any time.

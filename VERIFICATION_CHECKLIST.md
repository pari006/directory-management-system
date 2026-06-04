# Verification Checklist

Run these checks before pushing to GitHub.

## Automated Checks

```powershell
cd backend
python -m pytest -q
python -B -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for root in ('app','tests') for p in pathlib.Path(root).rglob('*.py')]; print('syntax ok')"

cd ..\frontend
npm install
npm run build
```

## Backend Coverage Included

The current `backend/tests/test_api.py` integration suite verifies:

- `/health`
- company admin signup and JWT login state
- employee create, list, detail, update, and delete
- employee permission denial for admin-only employee creation
- leave request validation, creation, company queue, approval, and balance update
- payroll summary for a company admin
- company billing simulation and company ledger
- super admin login, company listing, platform billing simulation, billing ledger, company suspension, and suspended-company login blocking

## Manual Browser Smoke Test

After backend and frontend are running:

1. Open the landing page.
2. Create a company account.
3. Add an employee from the directory.
4. Sign in as an employee and submit leave.
5. Sign in as company admin and approve/reject the leave.
6. Open payroll and record a payment run.
7. Sign in as super admin and confirm company/billing controls.

## GitHub Readiness

Confirmed ignore targets:

- `.env` and local secrets
- `.venv`, `node_modules`, and build output
- Python caches and pytest caches
- logs and local database files
- smoke-test artifacts

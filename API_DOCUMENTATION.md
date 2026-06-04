# API Documentation

The FastAPI app is mounted from `backend/app/main.py`. Each router is available under both `/api` and `/api/v1`.

Live docs are available when the backend is running:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Response Envelope

Most successful business endpoints return:

```json
{
  "success": true,
  "message": "Operation completed",
  "data": {}
}
```

Validation, auth, tenant, conflict, and database errors are normalized by `backend/app/core/exceptions.py`.

## Auth

Base path: `/api/v1/auth`

- `POST /signup`: create a company admin when no `company_id` is supplied, or create an employee inside an existing company when `company_id` is supplied.
- `POST /login`: unified login for super admins and company employees.
- `POST /company/login`: company admin/employee login.
- `POST /superadmin/login`: platform admin login.
- `POST /company/register`: explicit company registration with primary company admin.

Tokens include role and tenant claims. Company users receive `company_id` and `employee_id` claims.

## Employees

Base path: `/api/v1/employees`

- `POST /`: company admin creates an employee with optional compensation and leave allowance.
- `GET /`: list company employees with pagination, search, and sorting by `first_name`, `last_name`, or `email`.
- `GET /{employee_id}`: view employee details inside the current tenant.
- `PUT /{employee_id}`: company admin updates profile, compensation, and leave allowance.
- `DELETE /{employee_id}`: company admin deletes an employee.

## Leaves

Base path: `/api/v1/leaves`

- `POST /request`: employee submits a leave request.
- `GET /my-requests`: employee views their own leave requests.
- `GET /company`: company admin views all company leave requests.
- `PATCH /{leave_request_id}/approve`: company admin approves or rejects a request.
- `GET /{employee_id}/balance`: employee self-view or company admin leave balance lookup.

## Payroll

Mounted under `/api/v1/admin/payroll`.

- `GET /summary`: company admin payroll headcount and total salary overhead.

## Billing

Base path: `/api/v1/billing`

- `GET /company/ledger`: company admin views company payment ledger.
- `POST /company/simulate`: company admin records a simulated payment run.
- `GET /ledger`: super admin views all billing ledger rows.
- `POST /simulate`: super admin records simulated billing for a company UUID.

## Super Admin

Base path: `/api/v1/superadmin`

- `GET /companies`: platform company list with billing summary fields.
- `POST /companies/{company_id}/toggle-status`: toggle a company between active and suspended.

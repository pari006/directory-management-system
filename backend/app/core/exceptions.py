from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, IntegrityError


class TenantIsolationError(HTTPException):
    def __init__(self, message: str = "Unauthorized access to tenant data"):
        super().__init__(status_code=403, detail=message)


class InsufficientLeaveBalance(HTTPException):
    def __init__(self, message: str = "Insufficient leave balance for this request"):
        super().__init__(status_code=409, detail=message)


class DataLockTimeout(HTTPException):
    def __init__(self, message: str = "Database lock timeout. Please retry."):
        super().__init__(status_code=503, detail=message)


class BillingWebhookError(HTTPException):
    def __init__(self, message: str = "Invalid billing webhook"):
        super().__init__(status_code=400, detail=message)


class CompanyNotFound(HTTPException):
    def __init__(self, message: str = "Company not found"):
        super().__init__(status_code=404, detail=message)


class EmployeeNotFound(HTTPException):
    def __init__(self, message: str = "Employee not found"):
        super().__init__(status_code=404, detail=message)


class LeaveRequestNotFound(HTTPException):
    def __init__(self, message: str = "Leave request not found"):
        super().__init__(status_code=404, detail=message)


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "message": "Data integrity violation",
                "error_code": "INTEGRITY_ERROR",
                "details": str(exc.orig),
            },
        )

    @app.exception_handler(OperationalError)
    async def db_operational_error_handler(_: Request, exc: OperationalError):
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "Database unavailable or timeout",
                "error_code": "DB_TIMEOUT",
                "details": str(exc.orig),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):
        error_code = "HTTP_ERROR"
        if exc.status_code == 404:
            error_code = "NOT_FOUND"
        elif exc.status_code == 403:
            error_code = "FORBIDDEN"
        elif exc.status_code == 401:
            error_code = "UNAUTHORIZED"
        elif exc.status_code == 409:
            error_code = "CONFLICT"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": str(exc.detail),
                "error_code": error_code,
            },
        )


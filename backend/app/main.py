import asyncio
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.api.routes import auth, billing, employees, leaves, payroll, superadmin
from app.core.config import settings
from app.core.database import Base, async_engine, init_rls_policies
from app.core.exceptions import install_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await init_rls_policies(conn)
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

install_exception_handlers(app)

allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIXES = ("/api", "/api/v1")

for prefix in API_PREFIXES:
    app.include_router(auth.router, prefix=prefix)
    app.include_router(employees.router, prefix=prefix)
    app.include_router(leaves.router, prefix=prefix)
    app.include_router(payroll.router, prefix=f"{prefix}/admin")
    app.include_router(superadmin.router, prefix=prefix)
    app.include_router(billing.router, prefix=prefix)


@app.get("/health")
def health():
    return {"status": "ok"}

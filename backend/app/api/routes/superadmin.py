from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_super_admin, get_db
from app.models.database_models import BillingLedger, BillingStatus, Company, SubscriptionStatus

router = APIRouter(prefix="/superadmin", tags=["SuperAdmin"])


@router.get("/companies", status_code=status.HTTP_200_OK, summary="List all companies (Super Admin only)")
async def list_companies(
    admin=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all tenant companies registered on the platform."""
    stmt = select(Company).order_by(Company.created_at.desc())
    res = await db.execute(stmt)
    companies = res.scalars().all()

    ledger_res = await db.execute(select(BillingLedger))
    billing_by_company = {}
    for entry in ledger_res.scalars().all():
        summary = billing_by_company.setdefault(
            entry.company_id,
            {
                "paid_amount": 0.0,
                "pending_amount": 0.0,
                "failed_amount": 0.0,
                "latest_billing_status": None,
                "latest_billing_date": None,
            },
        )
        amount = float(entry.amount_simulated or 0)
        if entry.status == BillingStatus.PAID:
            summary["paid_amount"] += amount
        elif entry.status == BillingStatus.PENDING:
            summary["pending_amount"] += amount
        elif entry.status == BillingStatus.FAILED:
            summary["failed_amount"] += amount

        if summary["latest_billing_date"] is None or entry.billing_date > summary["latest_billing_date"]:
            summary["latest_billing_status"] = entry.status.value
            summary["latest_billing_date"] = entry.billing_date

    return [
        {
            "id": str(c.id),
            "company_name": c.company_name,
            "domain": c.domain,
            "subscription_status": c.subscription_status.value,
            "created_at": c.created_at.isoformat(),
            **{
                key: (value.isoformat() if key == "latest_billing_date" and value else value)
                for key, value in billing_by_company.get(
                    c.id,
                    {
                        "paid_amount": 0.0,
                        "pending_amount": 0.0,
                        "failed_amount": 0.0,
                        "latest_billing_status": None,
                        "latest_billing_date": None,
                    },
                ).items()
            },
        }
        for c in companies
    ]


@router.post("/companies/{company_id}/toggle-status", status_code=status.HTTP_200_OK)
async def toggle_company_status(
    company_id: UUID,
    admin=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Company).where(Company.id == company_id)
    res = await db.execute(stmt)
    company = res.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    new_status = (
        SubscriptionStatus.ACTIVE if company.subscription_status == SubscriptionStatus.SUSPENDED else SubscriptionStatus.SUSPENDED
    )

    stmt_up = update(Company).where(Company.id == company_id).values(subscription_status=new_status)
    await db.execute(stmt_up)
    await db.flush()

    return {"company_id": str(company_id), "subscription_status": new_status.value}

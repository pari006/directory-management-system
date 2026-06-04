from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_company_admin, require_super_admin, get_db
from app.models.database_models import Company, BillingLedger, BillingStatus
from app.schemas.billing import BillingWebhookResponse

router = APIRouter(prefix="/billing", tags=["Billing"])


def _ledger_row(entry: BillingLedger, company: Company) -> dict:
    return {
        "id": str(entry.id),
        "company_id": str(entry.company_id),
        "company_name": company.company_name,
        "amount": float(entry.amount_simulated),
        "status": entry.status.value,
        "billing_date": entry.billing_date.isoformat()
    }


@router.get("/ledger", status_code=status.HTTP_200_OK, summary="Get billing ledger entries")
async def get_billing_ledger(
    admin=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all simulated billing ledger entries across all companies (Super Admin only)."""
    stmt = select(BillingLedger, Company).join(Company).order_by(BillingLedger.billing_date.desc())
    res = await db.execute(stmt)
    results = res.all()
    return [
        _ledger_row(b, c)
        for b, c in results
    ]


@router.get("/company/ledger", status_code=status.HTTP_200_OK, summary="Get company payment ledger")
async def get_company_billing_ledger(
    current_admin=Depends(require_company_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve simulated payroll/payment ledger entries for the logged-in company admin."""
    stmt = (
        select(BillingLedger, Company)
        .join(Company)
        .where(BillingLedger.company_id == current_admin.company_id)
        .order_by(BillingLedger.billing_date.desc())
    )
    res = await db.execute(stmt)
    return [_ledger_row(entry, company) for entry, company in res.all()]


@router.post("/company/simulate", response_model=BillingWebhookResponse, status_code=status.HTTP_200_OK)
async def simulate_company_payment(
    amount: float,
    status: BillingStatus = BillingStatus.PAID,
    current_admin=Depends(require_company_admin),
    db: AsyncSession = Depends(get_db),
):
    """Record a simulated salary/payment run for the logged-in company."""
    ledger = BillingLedger(
        company_id=current_admin.company_id,
        amount_simulated=amount,
        status=status,
    )
    db.add(ledger)
    await db.flush()

    return BillingWebhookResponse(success=True, message="Company payment run recorded")


@router.post("/simulate", response_model=BillingWebhookResponse, status_code=status.HTTP_200_OK)
async def simulate_billing(
    company_id: UUID,
    amount: float,
    status: BillingStatus,
    admin=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Company).where(Company.id == company_id)
    res = await db.execute(stmt)
    company = res.scalar_one_or_none()
    if not company:
        return BillingWebhookResponse(success=False, message="Company not found")

    ledger = BillingLedger(company_id=company.id, amount_simulated=amount, status=status)
    db.add(ledger)
    await db.flush()

    return BillingWebhookResponse(success=True, message="Simulated billing recorded")

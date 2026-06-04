from typing import Optional
from pydantic import BaseModel, Field


class StripeWebhookEvent(BaseModel):
    type: str = Field(..., description="Event type (e.g., 'invoice.payment_succeeded', 'invoice.payment_failed')")
    data: dict = Field(..., description="Event data payload")


class StripeWebhookSchema(BaseModel):
    event_type: str = Field(..., description="Type of billing event")
    customer_id: str = Field(..., description="Stripe customer ID")
    amount: Optional[float] = Field(None, description="Amount in cents")
    status: str = Field(..., description="Event status (e.g., 'succeeded', 'failed')")

    model_config = {"json_schema_extra": {"example": {
        "event_type": "invoice.payment_failed",
        "customer_id": "cus_123456",
        "amount": 50000,
        "status": "failed"
    }}}


class BillingWebhookResponse(BaseModel):
    success: bool
    message: str
    event_id: Optional[str] = None

    model_config = {"json_schema_extra": {"example": {
        "success": True,
        "message": "Webhook processed successfully"
    }}}

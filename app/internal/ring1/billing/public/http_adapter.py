import secrets
from typing import Dict, Any, Optional
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from app.internal.ring0.protected.context import set_tenant_context, clear_tenant_context
from app.internal.ring1.billing.pure.invoice import Invoice, InvoiceStatus

router = APIRouter(prefix="/billing", tags=["Billing Layer"])

# Simple in-memory storage adapter meeting the domain boundary requirements
_mock_invoice_db: Dict[str, Invoice] = {}

class InvoiceRequest(BaseModel):
    """Validates inbound HTTP invoice creation payloads."""
    order_id: str
    amount: float

@router.post("/invoices")
async def create_invoice(
    payload: InvoiceRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID")
) -> Dict[str, Any]:
    """Generates an initial unpaid invoice under absolute multi-tenant bounds."""
    token = set_tenant_context(x_tenant_id)
    try:
        invoice_id = f"inv_{secrets.token_hex(4)}"
        invoice = Invoice(
            id=invoice_id,
            order_id=payload.order_id,
            tenant_id=x_tenant_id,
            amount=payload.amount,
            status=InvoiceStatus.UNPAID
        )
        
        # Persist to local domain storage state
        _mock_invoice_db[invoice_id] = invoice
        
        return {
            "status": "CREATED",
            "invoice_id": invoice.id,
            "state": invoice.status.value
        }
    finally:
        clear_tenant_context(token)

@router.post("/invoices/{invoice_id}/pay")
async def pay_invoice(
    invoice_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID")
) -> Dict[str, Any]:
    """Mutates invoice state to PAID through strict pure domain invariants."""
    token = set_tenant_context(x_tenant_id)
    try:
        invoice = _mock_invoice_db.get(invoice_id)
        if invoice is None or invoice.tenant_id != x_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice allocation missing within this tenant workspace."
            )
            
        try:
            # Execute business logic state shift on the pure object
            paid_invoice = invoice.mark_as_paid()
            _mock_invoice_db[invoice_id] = paid_invoice
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
            
        return {
            "status": "SUCCESS",
            "message": "Invoice balance cleared successfully.",
            "current_state": paid_invoice.status.value
        }
    finally:
        clear_tenant_context(token)
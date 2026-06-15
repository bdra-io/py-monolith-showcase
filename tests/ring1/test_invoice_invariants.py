import pytest
from app.internal.ring1.billing.pure.invoice import Invoice, InvoiceStatus

def test_invoice_creation_invariants() -> None:
    """Verifies that a scaffolded invoice initializes with a default unpaid state."""
    invoice = Invoice(
        id="inv_test_123",
        order_id="ord_abc",
        tenant_id="tenant_alpha",
        amount=250.00,
        status=InvoiceStatus.UNPAID
    )
    assert invoice.status == InvoiceStatus.UNPAID
    assert invoice.amount == 250.00


def test_invoice_successful_payment_mutation() -> None:
    """Ensures a valid unpaid invoice transitions cleanly to a paid state immutably."""
    invoice = Invoice(
        id="inv_test_123",
        order_id="ord_abc",
        tenant_id="tenant_alpha",
        amount=250.00,
        status=InvoiceStatus.UNPAID
    )
    
    paid_invoice = invoice.mark_as_paid()
    
    # Assert state mutation occurred correctly
    assert paid_invoice.status == InvoiceStatus.PAID
    # Assert absolute immutability (the original record must remain untouched!)
    assert invoice.status == InvoiceStatus.UNPAID


def test_invoice_payment_rejects_negative_balances() -> None:
    """Guarantees that pure domain business rules block processing of null or negative balances."""
    invoice = Invoice(
        id="inv_test_bad",
        order_id="ord_abc",
        tenant_id="tenant_alpha",
        amount=-50.00,
        status=InvoiceStatus.UNPAID
    )
    
    with pytest.raises(ValueError, match="Cannot process payments for null or negative balances."):
        invoice.mark_as_paid()
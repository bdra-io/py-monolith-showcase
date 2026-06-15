from dataclasses import dataclass
from enum import Enum

class InvoiceStatus(Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"


@dataclass(frozen=True)
class Invoice:
    """Pure domain structure representing a multi-tenant customer invoice."""
    id: str
    order_id: str
    tenant_id: str
    amount: float
    status: InvoiceStatus

    def mark_as_paid(self) -> "Invoice":
        """Immutable state mutation transitioning the invoice status safely."""
        if self.amount <= 0:
            raise ValueError("Cannot process payments for null or negative balances.")
        return Invoice(
            id=self.id,
            order_id=self.order_id,
            tenant_id=self.tenant_id,
            amount=self.amount,
            status=InvoiceStatus.PAID
        )
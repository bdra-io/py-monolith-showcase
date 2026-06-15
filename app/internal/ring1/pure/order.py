from dataclasses import dataclass
from datetime import datetime, timezone

class InvalidAmountError(ValueError):
    """Business rule violation exception for pure invariant math verification."""
    pass

@dataclass(frozen=True)
class Order:
    """Order represents the completely isolated domain state structure."""
    id: str
    user_id: str
    amount: float
    status: str
    created_at: datetime

def create_order(order_id: str, user_id: str, amount: float) -> Order:
    """Pure function executing business validation invariants with zero side effects."""
    if amount <= 0:
        raise InvalidAmountError("Order amount must be greater than zero.") #
        
    return Order(
        id=order_id,
        user_id=user_id,
        amount=amount,
        status="PENDING", #
        created_at=datetime.now(timezone.utc)
    )
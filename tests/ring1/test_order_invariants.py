import pytest
from app.internal.ring1.pure.order import create_order, InvalidAmountError

def test_create_order_with_valid_invariants() -> None:
    """Verifies that an order compiles in pending status under correct conditions."""
    order = create_order(
        order_id="ord_test123",
        user_id="usr_tenant99",
        amount=250.75
    )
    assert order.id == "ord_test123"
    assert order.user_id == "usr_tenant99"
    assert order.amount == 250.75
    assert order.status == "PENDING" # 
    assert order.created_at is not None

def test_create_order_rejects_invalid_zero_amount() -> None:
    """Enforces the invariant rule that values must exceed zero."""
    with pytest.raises(InvalidAmountError) as exc_info:
        create_order(
            order_id="ord_fail",
            user_id="usr_tenant99",
            amount=0.00
        )
    assert "greater than zero" in str(exc_info.value) # 

def test_create_order_rejects_negative_amount() -> None:
    """Guarantees negative ledger mutations are intercepted at the invariant boundary."""
    with pytest.raises(InvalidAmountError):
        create_order(
            order_id="ord_negative",
            user_id="usr_tenant99",
            amount=-50.25
        )
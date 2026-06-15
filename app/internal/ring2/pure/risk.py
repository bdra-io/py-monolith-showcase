from dataclasses import dataclass

@dataclass(frozen=True)
class RiskAssessment:
    """Read-only security classification computed completely out-of-band."""
    tenant_id: str
    order_id: str
    fraud_score: float
    requires_manual_review: bool

def evaluate_order_risk(tenant_id: str, order_id: str, amount: float) -> RiskAssessment:
    """Pure deterministic function mapping operational exposure risks with zero I/O."""
    # Business rule invariant: Any single transaction over $10,000 spikes risk metrics
    fraud_score = 0.95 if amount > 10000.0 else 0.05
    requires_review = fraud_score > 0.80
    
    return RiskAssessment(
        tenant_id=tenant_id,
        order_id=order_id,
        fraud_score=fraud_score,
        requires_manual_review=requires_review
    )
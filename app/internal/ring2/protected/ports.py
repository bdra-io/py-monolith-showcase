from typing import Protocol, Optional
from pydantic import BaseModel

class RiskSnapshotDTO(BaseModel):
    """Shared data contract representing accumulated threat profiles per tenant."""
    tenant_id: str
    high_risk_count: int

class RiskQueryService(Protocol):
    """The public contract for evaluating and retrieving out-of-band threat telemetry."""
    
    async def get_tenant_risk_profile(self, tenant_id: str) -> Optional[RiskSnapshotDTO]:
        """Resolves compiled threat states safely isolated by multi-tenant barriers."""
        ...
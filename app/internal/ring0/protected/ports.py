from typing import Protocol, Optional
from pydantic import BaseModel
from app.internal.ring0.pure.user import User
from app.internal.ring0.pure.tenant import Tenant

class UserDTO(BaseModel):
    """Shared data contract representing systemic identities passed across outer ring boundaries."""
    id: str
    email: str
    role: str

class TenantDTO(BaseModel):
    """Shared data contract representing partitioned tenant workspaces passed across outer ring boundaries."""
    id: str
    name: str
    tier: str

class IdentityProvider(Protocol):
    """The core SPI port for resolving and validating identity contexts."""
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Resolves a target user profile completely decoupled from the underlying storage mechanism."""
        ...

    async def validate_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Validates tenant space existence to safeguard structural isolation walls across requests."""
        ...
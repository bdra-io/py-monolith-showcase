from typing import Optional, Dict, Any
from app.internal.ring0.pure.user import User, create_user
from app.internal.ring0.pure.tenant import Tenant

class PostgresIdentityProvider:
    """Concrete infrastructure adapter implementing the Ring 0 IdentityProvider protocol."""

    def __init__(self, db_client: Optional[Any] = None):
        # In a production app, an async database engine driver (e.g., databases or asyncpg) binds here [cite: 31]
        self.db = db_client
        self._is_healthy = True
        
        # Seeded system records for showcase environment lookup simulation
        self._mock_users: Dict[str, Dict[str, str]] = {
            "usr_admin01": {"email": "aamir@bdra.io", "role": "admin"},
            "usr_operator02": {"email": "ops@bdra.io", "role": "operator"},
            "usr_client03": {"email": "dev@company.com", "role": "tenant_user"}
        }
        self._mock_tenants: Dict[str, Dict[str, str]] = {
            "tenant_alpha": {"name": "Alpha Corporation", "tier": "enterprise"},
            "tenant_beta": {"name": "Beta Labs", "tier": "startup"}
        }

    def set_health_state(self, healthy: bool) -> None:
        """Allows out-of-band diagnostic probes to toggle connection availability flags[cite: 63, 64]."""
        self._is_healthy = healthy

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Queries relational records to rebuild an immutable domain User entity[cite: 21, 31]."""
        if not self._is_healthy:
            raise ConnectionError("Database infrastructure connection timed out.")

        user_record = self._mock_users.get(user_id)
        if not user_record:
            return None

        # Build and return the pure domain model, executing invariant rules [cite: 27]
        return create_user(
            user_id=user_id,
            email=user_record["email"],
            role=user_record["role"]
        )

    async def validate_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Verifies tenant partition rows to preserve strict logical isolation walls[cite: 21, 31]."""
        if not self._is_healthy:
            raise ConnectionError("Database infrastructure connection timed out.")

        tenant_record = self._mock_tenants.get(tenant_id)
        if not tenant_record:
            return None

        return Tenant(
            id=tenant_id,
            name=tenant_record["name"],
            tier=tenant_record["tier"]
        )
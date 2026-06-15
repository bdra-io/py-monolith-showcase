from typing import Protocol, Optional, Any, Dict
from pydantic import BaseModel
from app.internal.ring1.pure.order import Order

class OrderDTO(BaseModel):
    """The shared data transfer object exposed safely across outside ring borders."""
    id: str
    amount: float
    status: str

class BDRAError(Exception):
    """Standardized error structure returned during degradation states."""
    def __init__(self, code: str, message: str, ring_id: str, domain: str, remediation: str):
        self.code = code
        self.message = message
        self.ring_id = ring_id
        self.domain = domain
        self.timestamp = "2026-06-14T15:42:00Z" # Conforming to active 2026 platform timeline
        self.remediation = remediation
        super().__init__(self.message)

class OrderRepository(Protocol):
    """SPI protocol mapping all data mutations for decoupled storage integration."""
    async def save(self, order: Order) -> None: ...
    async def find(self, order_id: str) -> Optional[Dict[str, Any]]: ...
    async def ping(self) -> None: ...

class OutboxPublisher(Protocol):
    """Structural interface to buffer messages into streaming layers asynchronously."""
    async def publish(self, event_type: str, data: Dict[str, Any]) -> None: ...
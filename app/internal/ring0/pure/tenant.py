from dataclasses import dataclass

@dataclass(frozen=True)
class Tenant:
    """Core Identity structure representing database tenant partitioning rules."""
    id: str
    name: str
    tier: str
from dataclasses import dataclass
from datetime import datetime, timezone
import re

class InvalidEmailError(ValueError):
    """Raised when an identity email fails regex structure validation rules."""
    pass

class InvalidRoleError(ValueError):
    """Raised when an assigned identity role breaches valid authorization scopes."""
    pass

@dataclass(frozen=True)
class User:
    """User represents the isolated core domain model for systemic identity."""
    id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

# Strict stateless business invariant constraints
VALID_ROLES = {"admin", "operator", "tenant_user"}
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def create_user(user_id: str, email: str, role: str) -> User:
    """Acts as a pure function executing business identity validation invariants."""
    clean_email = email.strip()
    if not EMAIL_REGEX.match(clean_email):
        raise InvalidEmailError(f"Provided address '{email}' is not a structurally valid email.")
        
    if role not in VALID_ROLES:
        raise InvalidRoleError(f"Role '{role}' is outside authorized system boundaries.")
        
    return User(
        id=user_id,
        email=clean_email,
        role=role,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
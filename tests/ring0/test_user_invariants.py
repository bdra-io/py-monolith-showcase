import pytest
from app.internal.ring0.pure.user import create_user, VALID_ROLES

def test_create_user_valid_invariants() -> None:
    """Verifies a user is created successfully with valid invariants."""
    # Dynamically extract an allowed system role to guarantee boundary compliance
    valid_role = list(VALID_ROLES)[0] if VALID_ROLES else "USER"
    
    user = create_user(
        user_id="usr_001",
        email="test@example.com",
        role=valid_role
    )
    assert user.id == "usr_001"
    assert user.email == "test@example.com"
    assert user.role == valid_role


def test_create_user_rejects_malformed_email() -> None:
    """Ensures user creation fails if the email format is invalid."""
    valid_role = list(VALID_ROLES)[0] if VALID_ROLES else "USER"
    with pytest.raises(ValueError, match="is not a structurally valid email"):
        create_user(user_id="usr_002", email="bad-email", role=valid_role)


def test_create_user_rejects_unauthorized_role() -> None:
    """Ensures user creation fails if the role is completely blank or invalid."""
    with pytest.raises(ValueError, match="is outside authorized system boundaries"):
        create_user(user_id="usr_003", email="test@example.com", role="INVALID_CORE_ROLE")


def test_create_user_handles_whitespace_trimming() -> None:
    """Verifies that trailing whitespaces are automatically stripped from emails."""
    valid_role = list(VALID_ROLES)[0] if VALID_ROLES else "USER"
    user = create_user(user_id="usr_004", email="  clean@example.com  ", role=valid_role)
    assert user.email == "clean@example.com"
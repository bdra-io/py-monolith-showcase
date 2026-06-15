import pytest
from app.internal.ring0.pure.user import create_user

def test_create_user_valid_invariants() -> None:
    """Verifies a user is created successfully with valid invariants."""
    user = create_user(
        user_id="usr_001",
        email="test@example.com",
        role="DEVELOPER"
    )
    assert user.id == "usr_001"
    assert user.email == "test@example.com"
    assert user.role == "DEVELOPER"


def test_create_user_rejects_malformed_email() -> None:
    """Ensures user creation fails if the email format is invalid."""
    with pytest.raises(ValueError, match="Invalid email address format"):
        create_user(user_id="usr_002", email="bad-email", role="DEVELOPER")


def test_create_user_rejects_unauthorized_role() -> None:
    """Ensures user creation fails if the role is completely blank or invalid."""
    with pytest.raises(ValueError, match="User role tracking assignment required"):
        create_user(user_id="usr_003", email="test@example.com", role="")


def test_create_user_handles_whitespace_trimming() -> None:
    """Verifies that trailing whitespaces are automatically stripped from emails."""
    user = create_user(user_id="usr_004", email="  clean@example.com  ", role="ADMIN")
    assert user.email == "clean@example.com"
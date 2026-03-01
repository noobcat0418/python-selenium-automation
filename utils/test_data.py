"""Test data constants and generators for E2E tests."""

from faker import Faker

fake = Faker()

# Pre-seeded users (must match app/models.py)
VALID_USER = {
    "email": "demo@example.com",
    "password": "Password123!",
    "name": "Demo User",
}

ADMIN_USER = {
    "email": "admin@example.com",
    "password": "AdminPass456!",
    "name": "Admin User",
}

INVALID_USER = {
    "email": "demo@example.com",
    "password": "WrongPassword999!",
}

NONEXISTENT_USER = {
    "email": "nobody@example.com",
    "password": "DoesNotExist1!",
}


def generate_random_user() -> dict:
    """Generate random user data for registration tests."""
    return {
        "email": fake.email(),
        "password": f"Test@{fake.random_number(digits=8)}",
        "name": fake.name(),
    }

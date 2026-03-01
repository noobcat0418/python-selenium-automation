"""Data models and in-memory stores for the mock auth server."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import bcrypt


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


@dataclass
class User:
    email: str
    hashed_password: str
    name: str
    provider: str = "local"  # "local", "google", "microsoft"

    def verify_password(self, password: str) -> bool:
        return _verify_password(password, self.hashed_password)


@dataclass
class RateLimitEntry:
    attempts: int = 0
    locked_until: Optional[datetime] = None


@dataclass
class OAuthState:
    provider: str
    created_at: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# In-memory stores (reset between tests via /api/reset)
# ---------------------------------------------------------------------------

# Pre-seeded test users
_DEFAULT_USERS = {
    "demo@example.com": User(
        email="demo@example.com",
        hashed_password=_hash_password("Password123!"),
        name="Demo User",
    ),
    "admin@example.com": User(
        email="admin@example.com",
        hashed_password=_hash_password("AdminPass456!"),
        name="Admin User",
    ),
}

users: dict[str, User] = dict(_DEFAULT_USERS)
rate_limits: dict[str, RateLimitEntry] = {}
oauth_states: dict[str, OAuthState] = {}


def reset_stores() -> None:
    """Reset all in-memory stores to defaults. Called by /api/reset."""
    users.clear()
    for email, user in _DEFAULT_USERS.items():
        users[email] = User(
            email=user.email,
            hashed_password=user.hashed_password,
            name=user.name,
            provider=user.provider,
        )
    rate_limits.clear()
    oauth_states.clear()

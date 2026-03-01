"""JWT token management and rate limiting logic."""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from app.models import RateLimitEntry, rate_limits

JWT_SECRET = "test-secret-key-for-e2e-testing-only"
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_MINUTES = 30

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 30


def create_access_token(
    email: str,
    name: str,
    provider: str = "local",
    expires_minutes: Optional[int] = None,
) -> str:
    """Create a signed JWT token."""
    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes or TOKEN_EXPIRY_MINUTES
    )
    payload = {
        "sub": email,
        "name": name,
        "provider": provider,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_short_lived_token(email: str, name: str, seconds: int = 5) -> str:
    """Create a token that expires in a few seconds (for testing expiration)."""
    expire = datetime.utcnow() + timedelta(seconds=seconds)
    payload = {
        "sub": email,
        "name": name,
        "provider": "local",
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def check_rate_limit(email: str) -> tuple[bool, Optional[str]]:
    """Check if login is rate-limited.

    Returns (is_locked, message).
    """
    entry = rate_limits.get(email)
    if entry is None:
        return False, None

    if entry.locked_until and datetime.utcnow() < entry.locked_until:
        remaining = (entry.locked_until - datetime.utcnow()).seconds
        return True, f"Account locked. Try again in {remaining} seconds."

    # Lockout has expired — reset
    if entry.locked_until and datetime.utcnow() >= entry.locked_until:
        rate_limits.pop(email, None)
        return False, None

    return False, None


def record_failed_attempt(email: str) -> tuple[bool, Optional[str]]:
    """Record a failed login attempt. Returns (is_now_locked, message)."""
    if email not in rate_limits:
        rate_limits[email] = RateLimitEntry()

    entry = rate_limits[email]
    entry.attempts += 1

    if entry.attempts >= MAX_ATTEMPTS:
        entry.locked_until = datetime.utcnow() + timedelta(seconds=LOCKOUT_SECONDS)
        return True, f"Too many failed attempts. Account locked for {LOCKOUT_SECONDS} seconds."

    remaining = MAX_ATTEMPTS - entry.attempts
    return False, f"Invalid credentials. {remaining} attempts remaining."


def reset_failed_attempts(email: str) -> None:
    """Clear rate limit on successful login."""
    rate_limits.pop(email, None)

"""Mock OAuth provider logic for demo authentication flows."""

import secrets
from datetime import datetime

from app.models import OAuthState, User, _hash_password, oauth_states, users

PROVIDERS = {
    "google": {
        "name": "Google",
        "color": "#4285F4",
        "icon": "G",
        "demo_email_domain": "gmail-demo.example.com",
    },
    "microsoft": {
        "name": "Microsoft",
        "color": "#00A4EF",
        "icon": "M",
        "demo_email_domain": "outlook-demo.example.com",
    },
}


def get_provider_config(provider: str) -> dict | None:
    """Get display configuration for a mock OAuth provider."""
    return PROVIDERS.get(provider)


def generate_oauth_state(provider: str) -> str:
    """Generate a CSRF state token for an OAuth flow."""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = OAuthState(provider=provider, created_at=datetime.utcnow())
    return state


def validate_oauth_state(state: str) -> OAuthState | None:
    """Validate and consume an OAuth state token."""
    return oauth_states.pop(state, None)


def get_or_create_oauth_user(provider: str) -> User:
    """Get or create a mock user for the OAuth provider."""
    config = PROVIDERS[provider]
    email = f"demo-user@{config['demo_email_domain']}"

    if email not in users:
        users[email] = User(
            email=email,
            hashed_password=_hash_password(secrets.token_urlsafe(16)),
            name=f"{config['name']} Demo User",
            provider=provider,
        )

    return users[email]

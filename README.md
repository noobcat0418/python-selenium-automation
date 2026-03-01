# E2E Authentication Testing Suite

![Python](https://img.shields.io/badge/python-3.11-blue)
![Playwright](https://img.shields.io/badge/playwright-1.48-green)
![FastAPI](https://img.shields.io/badge/fastapi-0.115-orange)

End-to-end test automation suite for modern authentication flows. Built with **Playwright (Python)** and a **FastAPI mock auth server**, demonstrating E2E testing best practices for portfolio and freelance showcase.

> **Demo Mode**: All OAuth flows (Google, Microsoft) are simulated using mock endpoints. No real credentials or services are used.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Playwright E2E Tests                │
│  email_login · oauth_login · logout · session       │
│  protected_routes · rate_limiting · network          │
├─────────────────────────────────────────────────────┤
│                  Test Utilities                       │
│  auth_helpers · test_data · network_helpers          │
├─────────────────────────────────────────────────────┤
│            FastAPI Mock Auth Server (SUT)             │
│  JWT Auth · Mock OAuth · Rate Limiting · Templates   │
├─────────────────────────────────────────────────────┤
│                  Infrastructure                      │
│  GitHub Actions CI · Allure Reports · Config         │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.11** | Core language |
| **Playwright** | Browser automation with auto-wait |
| **Pytest** | Test runner and fixtures |
| **FastAPI** | Mock authentication server |
| **python-jose** | JWT token generation/validation |
| **bcrypt** | Password hashing |
| **Allure** | Test reporting with screenshots |
| **pytest-xdist** | Parallel test execution |
| **pytest-rerunfailures** | Automatic flaky test retries |
| **GitHub Actions** | CI/CD pipeline |

## Project Structure

```
├── app/                          # FastAPI mock auth server
│   ├── main.py                   # Routes and middleware
│   ├── auth.py                   # JWT and rate limiting logic
│   ├── models.py                 # Data models and user store
│   ├── oauth.py                  # Mock OAuth provider logic
│   ├── templates/                # Jinja2 HTML templates
│   └── static/                   # CSS styles
├── tests/                        # Playwright E2E tests
│   ├── conftest.py               # Server lifecycle and fixtures
│   ├── test_email_login.py       # Email/password auth tests
│   ├── test_oauth_login.py       # Mock OAuth flow tests
│   ├── test_logout.py            # Logout flow tests
│   ├── test_session.py           # Session management tests
│   ├── test_protected_routes.py  # Route protection tests
│   ├── test_rate_limiting.py     # Account lockout tests
│   └── test_network.py           # Network interception tests
├── utils/                        # Shared test utilities
│   ├── auth_helpers.py           # Reusable login/logout actions
│   ├── test_data.py              # Test user data and generators
│   └── network_helpers.py        # Route interception utilities
├── config/
│   └── config.yml                # Test configuration
├── .github/workflows/
│   └── e2e-tests.yml             # CI pipeline
├── pytest.ini                    # Pytest configuration
└── requirements.txt              # Python dependencies
```

## Setup

### Prerequisites
- Python 3.10+
- pip

### Install

```bash
git clone <repository-url>
cd python-selenium-automation
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Running Tests

The mock server starts automatically via the pytest `server` fixture — no manual startup needed.

### Run all tests
```bash
pytest
```

### Run smoke tests only
```bash
pytest -m smoke
```

### Run by category
```bash
pytest -m auth           # Email/password tests
pytest -m oauth          # OAuth flow tests
pytest -m session        # Session management tests
pytest -m security       # Rate limiting and injection tests
pytest -m network        # Network interception tests
```

### Run a specific test file
```bash
pytest tests/test_email_login.py -v
```

### Run in headed mode (see the browser)
```bash
pytest --headed
```

### Run in parallel
```bash
pytest -n auto
```

### Start the mock server manually (for development)
```bash
uvicorn app.main:app --reload --port 8000
```
Then visit `http://localhost:8000` to interact with the login UI.

## Test Scenarios

| Category | Tests | What's Covered |
|----------|-------|----------------|
| **Email Login** | 6 | Valid/invalid credentials, empty fields, SQL injection |
| **OAuth Login** | 5 | Google/Microsoft flows, consent screen, deny flow |
| **Logout** | 3 | Redirect, session clearing, post-logout access |
| **Session** | 4 | Persistence on reload, cross-page, expiration, API data |
| **Protected Routes** | 4 | Auth required, redirect preservation, public access |
| **Rate Limiting** | 3 | Lockout after failures, lockout enforcement, cooldown |
| **Network** | 3 | Error mocking, slow responses, request interception |
| **Total** | **28** | |

## Mock Auth Server Features

- **Email/password login** with bcrypt-hashed passwords
- **JWT tokens** in HTTP-only cookies
- **Mock OAuth flows** for Google and Microsoft with consent screens
- **Protected routes** (`/dashboard`, `/profile`) with auth middleware
- **Rate limiting** — account lockout after 5 failed attempts
- **Session expiration** — configurable token TTL
- **"DEMO MODE" banners** on all pages — clearly not impersonating real services
- **Test helper endpoints** (`/api/reset`, `/api/set-short-token`) for test isolation

## Reporting

### Generate Allure report
```bash
pytest --alluredir=reports/allure-results
allure serve reports/allure-results
```

Reports include:
- Test execution timeline
- Pass/fail breakdown by feature
- Screenshots and videos on failure
- Playwright trace files for debugging

## CI/CD

GitHub Actions runs automatically on push to main and PRs:

- **Smoke tests** — runs on every PR
- **Full suite** — runs on main branch pushes
- Uploads Allure results and failure artifacts

## Test Credentials

| User | Email | Password |
|------|-------|----------|
| Demo User | `demo@example.com` | `Password123!` |
| Admin User | `admin@example.com` | `AdminPass456!` |

"""Pytest fixtures for E2E authentication tests.

Manages the FastAPI mock server lifecycle and provides
Playwright page fixtures with test isolation.
"""

import subprocess
import sys
import time

import allure
import httpx
import pytest
from playwright.sync_api import Page

BASE_URL = "http://127.0.0.1:8000"


# ---------------------------------------------------------------------------
# Server lifecycle (session-scoped)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def server():
    """Start the FastAPI mock auth server for the test session."""
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--log-level", "warning",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready
    for _ in range(30):
        try:
            resp = httpx.get(f"{BASE_URL}/health", timeout=1)
            if resp.status_code == 200:
                break
        except httpx.ConnectError:
            time.sleep(0.5)
    else:
        proc.kill()
        raise RuntimeError("Mock auth server failed to start within 15 seconds")

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# ---------------------------------------------------------------------------
# Test isolation
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_server_state(server):
    """Reset server state before each test for isolation."""
    httpx.post(f"{BASE_URL}/api/reset", timeout=5)


# ---------------------------------------------------------------------------
# Playwright page fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_page(page: Page, server) -> Page:
    """Provide a Playwright page that's connected to the mock server."""
    page.set_default_timeout(10000)
    page.set_default_navigation_timeout(10000)
    return page


# ---------------------------------------------------------------------------
# Allure reporting hooks
# ---------------------------------------------------------------------------

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page = item.funcargs.get("auth_page") or item.funcargs.get("page")
        if page:
            try:
                screenshot = page.screenshot()
                allure.attach(
                    screenshot,
                    name="failure-screenshot",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception:
                pass

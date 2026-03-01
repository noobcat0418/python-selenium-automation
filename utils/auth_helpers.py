"""Reusable Playwright helpers for authentication flows."""

from playwright.sync_api import Page, expect


BASE_URL = "http://127.0.0.1:8000"


def login(page: Page, email: str, password: str) -> None:
    """Fill the login form and submit."""
    page.get_by_test_id("email-input").fill(email)
    page.get_by_test_id("password-input").fill(password)
    page.get_by_test_id("login-button").click()


def login_and_wait(page: Page, email: str, password: str) -> None:
    """Login and wait for navigation to complete."""
    login(page, email, password)
    page.wait_for_url("**/dashboard**")


def logout(page: Page) -> None:
    """Click logout and wait for login page."""
    page.get_by_test_id("logout-button").click()
    page.wait_for_url("**/login**")


def go_to_login(page: Page) -> None:
    """Navigate to the login page."""
    page.goto(f"{BASE_URL}/login")


def assert_on_dashboard(page: Page) -> None:
    """Assert the user is on the dashboard page."""
    expect(page).to_have_url(f"{BASE_URL}/dashboard")
    expect(page.get_by_test_id("welcome-message")).to_be_visible()


def assert_on_login(page: Page) -> None:
    """Assert the user is on the login page."""
    expect(page).to_have_url(f"{BASE_URL}/login", timeout=5000)


def assert_error_message(page: Page, text: str | None = None) -> None:
    """Assert an error message is visible, optionally matching text."""
    error = page.get_by_test_id("error-message")
    expect(error).to_be_visible()
    if text:
        expect(error).to_contain_text(text)


def get_session_info(page: Page) -> dict:
    """Fetch session info from the API."""
    response = page.request.get(f"{BASE_URL}/api/session-info")
    return response.json()

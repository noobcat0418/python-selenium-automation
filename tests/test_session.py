"""E2E tests for session persistence and expiration."""

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from utils.auth_helpers import (
    assert_on_dashboard,
    get_session_info,
    go_to_login,
    login_and_wait,
)
from utils.test_data import VALID_USER

BASE_URL = "http://127.0.0.1:8000"


@allure.feature("Session Management")
class TestSession:

    @pytest.mark.smoke
    @pytest.mark.session
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Session persists after page reload")
    def test_session_persists_on_reload(self, auth_page: Page):
        go_to_login(auth_page)
        login_and_wait(auth_page, VALID_USER["email"], VALID_USER["password"])

        # Reload page
        auth_page.reload()

        # Should still be on dashboard
        assert_on_dashboard(auth_page)

    @pytest.mark.session
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Session persists across page navigation")
    def test_session_persists_across_pages(self, auth_page: Page):
        go_to_login(auth_page)
        login_and_wait(auth_page, VALID_USER["email"], VALID_USER["password"])

        # Navigate to profile
        auth_page.get_by_test_id("profile-link").click()
        expect(auth_page).to_have_url(f"{BASE_URL}/profile")
        expect(auth_page.get_by_test_id("profile-name")).to_have_text(VALID_USER["name"])

        # Navigate back to dashboard
        auth_page.goto(f"{BASE_URL}/dashboard")
        assert_on_dashboard(auth_page)

    @pytest.mark.session
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Expired session redirects to login")
    def test_expired_session_redirects(self, auth_page: Page):
        go_to_login(auth_page)
        login_and_wait(auth_page, VALID_USER["email"], VALID_USER["password"])

        # Set a short-lived token (2 seconds)
        auth_page.request.post(
            f"{BASE_URL}/api/set-short-token",
            form={"email": VALID_USER["email"], "seconds": "2"},
        )

        # Wait for token to expire
        auth_page.wait_for_timeout(3000)

        # Try to access dashboard
        auth_page.goto(f"{BASE_URL}/dashboard")
        expect(auth_page).to_have_url(re.compile(r"/login"))

    @pytest.mark.session
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Session info API returns user data")
    def test_session_info_returns_user_data(self, auth_page: Page):
        go_to_login(auth_page)
        login_and_wait(auth_page, VALID_USER["email"], VALID_USER["password"])

        session = get_session_info(auth_page)
        assert session["authenticated"] is True
        assert session["email"] == VALID_USER["email"]
        assert session["name"] == VALID_USER["name"]
        assert session["provider"] == "local"

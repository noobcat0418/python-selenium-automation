"""E2E tests for logout flows."""

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from utils.auth_helpers import (
    assert_on_login,
    get_session_info,
    go_to_login,
    login_and_wait,
    logout,
)
from utils.test_data import VALID_USER

BASE_URL = "http://127.0.0.1:8000"


@allure.feature("Logout")
class TestLogout:

    @pytest.mark.smoke
    @pytest.mark.auth
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Logout redirects to login page")
    def test_logout_redirects_to_login(self, auth_page: Page):
        go_to_login(auth_page)
        login_and_wait(auth_page, VALID_USER["email"], VALID_USER["password"])
        logout(auth_page)

        assert_on_login(auth_page)

    @pytest.mark.auth
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Logout clears session data")
    def test_logout_clears_session(self, auth_page: Page):
        go_to_login(auth_page)
        login_and_wait(auth_page, VALID_USER["email"], VALID_USER["password"])

        # Verify session exists
        session = get_session_info(auth_page)
        assert session["authenticated"] is True

        logout(auth_page)

        # Session should be cleared
        response = auth_page.request.get(f"{BASE_URL}/api/session-info")
        assert response.status == 401

    @pytest.mark.auth
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Cannot access dashboard after logout")
    def test_cannot_access_dashboard_after_logout(self, auth_page: Page):
        go_to_login(auth_page)
        login_and_wait(auth_page, VALID_USER["email"], VALID_USER["password"])
        logout(auth_page)

        # Try to access dashboard directly
        auth_page.goto(f"{BASE_URL}/dashboard")
        expect(auth_page).to_have_url(re.compile(r"/login"))

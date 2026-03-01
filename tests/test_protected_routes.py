"""E2E tests for protected route access control."""

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from utils.auth_helpers import go_to_login, login, login_and_wait
from utils.test_data import VALID_USER

BASE_URL = "http://127.0.0.1:8000"


@allure.feature("Route Protection")
class TestProtectedRoutes:

    @pytest.mark.smoke
    @pytest.mark.auth
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Dashboard requires authentication")
    def test_dashboard_requires_auth(self, auth_page: Page):
        auth_page.goto(f"{BASE_URL}/dashboard")
        expect(auth_page).to_have_url(re.compile(r"/login"))

    @pytest.mark.auth
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Profile requires authentication")
    def test_profile_requires_auth(self, auth_page: Page):
        auth_page.goto(f"{BASE_URL}/profile")
        expect(auth_page).to_have_url(re.compile(r"/login"))

    @pytest.mark.auth
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Login page is accessible without authentication")
    def test_login_page_accessible_without_auth(self, auth_page: Page):
        auth_page.goto(f"{BASE_URL}/login")
        expect(auth_page).to_have_url(f"{BASE_URL}/login")
        expect(auth_page.get_by_test_id("login-form")).to_be_visible()

    @pytest.mark.auth
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Redirect preserves original destination after login")
    def test_redirect_to_original_url_after_login(self, auth_page: Page):
        # Try to access profile without auth
        auth_page.goto(f"{BASE_URL}/profile")

        # Should be redirected to login with ?next=/profile
        expect(auth_page).to_have_url(re.compile(r"/login\?next=/profile"))

        # Login
        login(auth_page, VALID_USER["email"], VALID_USER["password"])

        # Should land on profile (the original destination)
        auth_page.wait_for_url("**/profile")
        expect(auth_page.get_by_test_id("profile-name")).to_have_text(VALID_USER["name"])

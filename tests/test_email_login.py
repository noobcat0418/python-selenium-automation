"""E2E tests for email/password authentication flows."""

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from utils.auth_helpers import (
    assert_error_message,
    assert_on_dashboard,
    go_to_login,
    login,
    login_and_wait,
)
from utils.test_data import INVALID_USER, NONEXISTENT_USER, VALID_USER


@allure.feature("Email Authentication")
class TestEmailLogin:

    @pytest.mark.smoke
    @pytest.mark.auth
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Successful login redirects to dashboard")
    def test_successful_login(self, auth_page: Page):
        go_to_login(auth_page)
        login_and_wait(auth_page, VALID_USER["email"], VALID_USER["password"])

        assert_on_dashboard(auth_page)
        welcome = auth_page.get_by_test_id("welcome-message")
        expect(welcome).to_contain_text(VALID_USER["name"])

    @pytest.mark.smoke
    @pytest.mark.auth
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Invalid password shows error message")
    def test_invalid_password(self, auth_page: Page):
        go_to_login(auth_page)
        login(auth_page, INVALID_USER["email"], INVALID_USER["password"])

        assert_error_message(auth_page, "Invalid")
        expect(auth_page).to_have_url(re.compile(r"/login"), timeout=3000)

    @pytest.mark.auth
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Non-existent user shows error message")
    def test_nonexistent_user(self, auth_page: Page):
        go_to_login(auth_page)
        login(auth_page, NONEXISTENT_USER["email"], NONEXISTENT_USER["password"])

        assert_error_message(auth_page, "Invalid")

    @pytest.mark.auth
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Empty email field triggers validation")
    def test_empty_email(self, auth_page: Page):
        go_to_login(auth_page)
        auth_page.get_by_test_id("password-input").fill("somepassword")
        auth_page.get_by_test_id("login-button").click()

        # Browser's built-in validation prevents form submission
        email_input = auth_page.get_by_test_id("email-input")
        is_valid = email_input.evaluate("el => el.validity.valid")
        assert not is_valid, "Empty email should fail HTML validation"

    @pytest.mark.auth
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Empty password field triggers validation")
    def test_empty_password(self, auth_page: Page):
        go_to_login(auth_page)
        auth_page.get_by_test_id("email-input").fill("test@example.com")
        auth_page.get_by_test_id("login-button").click()

        password_input = auth_page.get_by_test_id("password-input")
        is_valid = password_input.evaluate("el => el.validity.valid")
        assert not is_valid, "Empty password should fail HTML validation"

    @pytest.mark.auth
    @pytest.mark.security
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("SQL injection attempt is safely handled")
    def test_sql_injection_attempt(self, auth_page: Page):
        go_to_login(auth_page)
        login(auth_page, "' OR '1'='1", "' OR '1'='1")

        # Should show error, not crash or bypass auth
        # The email field has type="email" so browser may block,
        # but the server should handle it safely regardless
        expect(auth_page).not_to_have_url(re.compile(r"/dashboard"))

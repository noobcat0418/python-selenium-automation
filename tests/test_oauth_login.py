"""E2E tests for mock OAuth authentication flows."""

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from utils.auth_helpers import assert_on_dashboard, assert_on_login, go_to_login


@allure.feature("OAuth Authentication")
class TestOAuthLogin:

    @pytest.mark.smoke
    @pytest.mark.oauth
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Google OAuth mock flow completes successfully")
    def test_google_oauth_flow(self, auth_page: Page):
        go_to_login(auth_page)
        auth_page.get_by_test_id("google-oauth-button").click()

        # Should land on consent screen
        expect(auth_page).to_have_url(re.compile(r"/oauth/google/consent"))
        expect(auth_page.get_by_test_id("oauth-demo-notice")).to_be_visible()

        # Allow access
        auth_page.get_by_test_id("oauth-allow-button").click()

        # Should redirect to dashboard
        assert_on_dashboard(auth_page)
        provider = auth_page.get_by_test_id("user-provider")
        expect(provider).to_have_text("google")

    @pytest.mark.smoke
    @pytest.mark.oauth
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Microsoft OAuth mock flow completes successfully")
    def test_microsoft_oauth_flow(self, auth_page: Page):
        go_to_login(auth_page)
        auth_page.get_by_test_id("microsoft-oauth-button").click()

        expect(auth_page).to_have_url(re.compile(r"/oauth/microsoft/consent"))
        auth_page.get_by_test_id("oauth-allow-button").click()

        assert_on_dashboard(auth_page)
        provider = auth_page.get_by_test_id("user-provider")
        expect(provider).to_have_text("microsoft")

    @pytest.mark.oauth
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("OAuth consent screen shows demo mode banner")
    def test_oauth_consent_shows_demo_banner(self, auth_page: Page):
        go_to_login(auth_page)
        auth_page.get_by_test_id("google-oauth-button").click()

        notice = auth_page.get_by_test_id("oauth-demo-notice")
        expect(notice).to_be_visible()
        expect(notice).to_contain_text("DEMO")
        expect(notice).to_contain_text("Not a real")

    @pytest.mark.oauth
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Denying OAuth consent returns to login with message")
    def test_oauth_deny(self, auth_page: Page):
        go_to_login(auth_page)
        auth_page.get_by_test_id("google-oauth-button").click()
        auth_page.get_by_test_id("oauth-deny-button").click()

        # Should be back on login page
        expect(auth_page).to_have_url(re.compile(r"/login"))

    @pytest.mark.oauth
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("OAuth login shows correct provider on dashboard")
    def test_oauth_login_shows_provider_name(self, auth_page: Page):
        go_to_login(auth_page)
        auth_page.get_by_test_id("microsoft-oauth-button").click()
        auth_page.get_by_test_id("oauth-allow-button").click()

        assert_on_dashboard(auth_page)
        email = auth_page.get_by_test_id("user-email")
        expect(email).to_contain_text("outlook-demo.example.com")

"""E2E tests for network interception and mocking."""

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from utils.auth_helpers import go_to_login, login_and_wait
from utils.network_helpers import mock_slow_response
from utils.test_data import VALID_USER

BASE_URL = "http://127.0.0.1:8000"


@allure.feature("Network Interception")
class TestNetwork:

    @pytest.mark.network
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Intercept and mock a server error response")
    def test_mock_server_error(self, auth_page: Page):
        go_to_login(auth_page)
        login_and_wait(auth_page, VALID_USER["email"], VALID_USER["password"])

        # Mock the session-info API to return 500 via page.route
        auth_page.route("**/api/session-info", lambda route: route.fulfill(
            status=500,
            content_type="application/json",
            body='{"error": "Mocked server error"}',
        ))

        # Fetch via page context (evaluate fetch) so it goes through page routes
        status = auth_page.evaluate("""
            async () => {
                const resp = await fetch('/api/session-info');
                return resp.status;
            }
        """)
        assert status == 500

    @pytest.mark.network
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Application handles slow network responses")
    def test_slow_network_response(self, auth_page: Page):
        # Add 2-second delay to login endpoint
        mock_slow_response(auth_page, "**/login", delay_ms=2000)

        go_to_login(auth_page)
        login_and_wait(auth_page, VALID_USER["email"], VALID_USER["password"])

        # Should still complete successfully (just slower)
        expect(auth_page).to_have_url(re.compile(r"/dashboard"))

    @pytest.mark.network
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Intercept and verify login request payload")
    def test_intercept_and_verify_request(self, auth_page: Page):
        # Capture only POST requests to /login
        captured_posts = []

        def handler(route):
            if route.request.method == "POST":
                captured_posts.append({
                    "url": route.request.url,
                    "method": route.request.method,
                    "post_data": route.request.post_data,
                })
            route.continue_()

        auth_page.route("**/login", handler)

        go_to_login(auth_page)
        login_and_wait(auth_page, VALID_USER["email"], VALID_USER["password"])

        # Verify the login POST was captured with correct data
        assert len(captured_posts) >= 1
        login_request = captured_posts[0]
        assert login_request["method"] == "POST"
        # Form data is URL-encoded, so @ becomes %40
        assert "email=" in login_request["post_data"]
        assert "demo" in login_request["post_data"]
        assert "example.com" in login_request["post_data"]

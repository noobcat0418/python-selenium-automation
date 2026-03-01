"""Network interception utilities for Playwright tests."""

import time
from playwright.sync_api import Page, Route


def mock_api_failure(page: Page, url_pattern: str, status: int = 500) -> None:
    """Intercept requests matching pattern and return an error status."""
    def handler(route: Route):
        route.fulfill(
            status=status,
            content_type="application/json",
            body='{"error": "Mocked server error"}',
        )
    page.route(url_pattern, handler)


def mock_slow_response(page: Page, url_pattern: str, delay_ms: int = 3000) -> None:
    """Intercept requests and add a delay before continuing."""
    def handler(route: Route):
        time.sleep(delay_ms / 1000)
        route.continue_()
    page.route(url_pattern, handler)


def block_requests(page: Page, url_pattern: str) -> None:
    """Abort all requests matching pattern."""
    page.route(url_pattern, lambda route: route.abort())


def capture_request(page: Page, url_pattern: str) -> list:
    """Capture requests matching pattern and return them as a list."""
    captured = []

    def handler(route: Route):
        captured.append({
            "url": route.request.url,
            "method": route.request.method,
            "post_data": route.request.post_data,
        })
        route.continue_()

    page.route(url_pattern, handler)
    return captured

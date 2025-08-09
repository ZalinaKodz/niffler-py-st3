import os
from typing import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from pages.login_page import AuthPage


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=os.getenv("HEADLESS", "false").lower() == "true",
            slow_mo=int(os.getenv("SLOW_MO", "0"))
        )
        yield browser
        browser.close()

@pytest.fixture
def context(browser: Browser, request: pytest.FixtureRequest) -> Generator[BrowserContext, None, None]:
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    yield context
    if request.node.rep_call.failed:
        test_name = request.node.name.replace("/", "_")
        page = context.pages[0]
        page.screenshot(path=f"artifacts/{test_name}.png", full_page=True)
    context.close()

@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    page = context.new_page()
    yield page
    page.close()

@pytest.fixture(scope="session")
def auth_context(browser: Browser, auth_url: str, frontend_url: str, settings) -> Generator[BrowserContext, None, None]:
    context = browser.new_context()
    page = context.new_page()
    auth_page = AuthPage(page, auth_url, frontend_url)
    auth_page.navigate_to_login()
    auth_page.login(settings.TEST_USERNAME, settings.TEST_PASSWORD)
    yield context
    context.close()

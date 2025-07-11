import os
import re

import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, expect
from faker import Faker
from typing import Generator
import logging
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError
from pages.profile_page import ProfilePage
from pages.login_page import AuthPage
from pages.signup_page import RegistrationPage
from pages.spending_page import SpendingPage

# Constants
DEFAULT_HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
DEFAULT_SLOW_MO = int(os.getenv("SLOW_MO", "0"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Validate environment variables"""
    AUTH_URL: str = Field(default="http://auth.niffler.dc:9000")
    FRONTEND_URL: str = Field(default="http://frontend.niffler.dc")
    GATEWAY_URL: str = Field(default="http://gateway.niffler.dc:8090")
    TEST_USERNAME: str
    TEST_PASSWORD: str

    class Config:
        env_file = ".env"


try:
    settings = Settings()
except ValidationError as e:
    logger.error(f"Environment validation error: {e}")
    raise

fake = Faker()


# Hooks
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# Core fixtures
@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """Launch browser instance (session-scoped)"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=DEFAULT_HEADLESS,
            slow_mo=DEFAULT_SLOW_MO
        )
        logger.info(f"Browser launched (headless={DEFAULT_HEADLESS})")
        yield browser
        browser.close()
        logger.info("Browser closed")


@pytest.fixture
def context(browser: Browser, request: pytest.FixtureRequest) -> Generator[BrowserContext, None, None]:
    """Browser context with automatic artifact collection on failure"""
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True,
        record_video_dir="videos" if os.getenv("RECORD_VIDEO") else None
    )
    yield context

    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        try:
            os.makedirs("artifacts", exist_ok=True)
            test_name = request.node.name.replace("/", "_")
            page = context.pages[0]
            page.screenshot(path=f"artifacts/{test_name}.png", full_page=True)

            if page.video:
                video_path = f"artifacts/{test_name}.webm"
                page.video.save_as(video_path)
                logger.info(f"Saved video: {video_path}")
        except Exception as e:
            logger.error(f"Failed to save artifacts: {e}")
    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """New browser page"""
    page = context.new_page()
    yield page
    page.close()


# Auth fixtures
@pytest.fixture(scope="session")
def auth_context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Authenticated browser context"""
    context = browser.new_context()
    page = context.new_page()
    auth_page = AuthPage(page)
    auth_page.navigate_to_login()
    auth_page.login(settings.TEST_USERNAME, settings.TEST_PASSWORD)
    yield context
    context.close()


@pytest.fixture
def auth_page(page: Page) -> AuthPage:
    """AuthPage instance"""
    return AuthPage(page).navigate_to_login()


# User management
class UserData(BaseSettings):
    username: str
    password: str
    firstname: str | None = None
    surname: str | None = None


@pytest.fixture
def unregistered_user() -> UserData:
    """Generate data for a new unregistered user"""
    username = f"{fake.unique.user_name()}_{os.getpid()}"
    user = UserData(
        username=username,
        password=fake.password(length=12),
        firstname=fake.first_name(),
        surname=fake.last_name()
    )
    logger.info(f"Generated unregistered user: {user.username}")
    return user


# Page object fixtures with auth
@pytest.fixture
def authenticated_page(auth_context: BrowserContext) -> Page:
    """Authenticated page instance"""
    return auth_context.new_page()


@pytest.fixture
def profile_page(authenticated_page: Page) -> ProfilePage:
    """ProfilePage instance"""
    profile = ProfilePage(authenticated_page)
    authenticated_page.goto(f"{settings.FRONTEND_URL}/profile")
    return profile


@pytest.fixture
def spending_page(authenticated_page: Page) -> SpendingPage:
    """SpendingPage instance"""
    spending_page = SpendingPage(authenticated_page)
    spending_page.navigate_to_spending()
    return spending_page


# Test data generators
@pytest.fixture
def random_category() -> str:
    """Generate random category name"""
    return f"{fake.word(part_of_speech='noun')} {fake.word(part_of_speech='noun')}"


@pytest.fixture
def random_amount() -> int:
    """Generate random amount"""
    return fake.random_int(100, 9999)

@pytest.fixture
def registration_page(page: Page) -> RegistrationPage:
    """RegistrationPage instance"""
    return RegistrationPage(page).navigate()


@pytest.fixture
def authenticated_page(page: Page) -> Page:
    """
    Фикстура возвращает авторизованную страницу
    Заменяет _login и auth_context
    """
    auth_page = AuthPage(page)

    # Навигация и авторизация
    auth_page.navigate_to_login()
    auth_page.login(
        username=os.getenv("TEST_USERNAME", "qwerty"),
        password=os.getenv("TEST_PASSWORD", "12345")
    )

    # Проверка успешной авторизации
    expect(page).to_have_url(re.compile(r".*/main"), timeout=10000)

    return page
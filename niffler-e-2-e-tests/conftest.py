import os
import pytest
import requests
from playwright.sync_api import sync_playwright, Page
from faker import Faker
from typing import Generator, Dict, Any
from dotenv import load_dotenv
import logging
from pages.profile_page import ProfilePage
from pages.login_page import AuthPage
from pages.signup_page import RegistrationPage
from pages.spending_page import SpendingPage

# Initial setup
load_dotenv()
fake = Faker()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
DEFAULT_SLOW_MO = int(os.getenv("SLOW_MO", "0"))
BASE_URLS = {
    "auth": os.getenv("AUTH_URL", "http://auth.niffler.dc:9000").rstrip("/"),
    "frontend": os.getenv("FRONTEND_URL", "http://frontend.niffler.dc").rstrip("/"),
    "api": os.getenv("GATEWAY_URL", "http://gateway.niffler.dc:8090").rstrip("/")
}


# Hooks
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook for test reporting and artifact collection"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# Core fixtures
@pytest.fixture(scope="session")
def browser():
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
def context(browser, request) -> Generator:
    """Browser context with automatic artifact collection on failure"""
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True,
        record_video_dir="videos" if os.getenv("RECORD_VIDEO") else None
    )
    yield context

    # Save artifacts on test failure
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        try:
            os.makedirs("artifacts", exist_ok=True)
            test_name = request.node.name.replace("/", "_")
            context.pages[0].screenshot(
                path=f"artifacts/{test_name}.png",
                full_page=True
            )
            if context.pages[0].video:
                context.pages[0].video.save_as(f"artifacts/{test_name}.webm")
            logger.info(f"Saved artifacts for failed test: {test_name}")
        except Exception as e:
            logger.error(f"Failed to save artifacts: {e}")

    context.close()


@pytest.fixture
def page(context) -> Generator[Page, None, None]:
    """New browser page"""
    page = context.new_page()
    yield page
    page.close()


# URL fixtures
@pytest.fixture(scope="session")
def auth_url() -> str:
    return BASE_URLS["auth"]


@pytest.fixture(scope="session")
def frontend_url() -> str:
    return BASE_URLS["frontend"]


@pytest.fixture(scope="session")
def api_url() -> str:
    return BASE_URLS["api"]


# User management fixtures
@pytest.fixture
def unregistered_user() -> Dict[str, str]:
    """Generate data for a new unregistered user"""
    user_data = {
        "username": f"user_{fake.user_name()}_{fake.random_int(1000, 9999)}",
        "password": fake.password(length=12),
        "firstname": fake.first_name(),
        "surname": fake.last_name()
    }
    logger.info(f"Generated unregistered user: {user_data['username']}")
    return user_data


@pytest.fixture(scope="session")
def cleanup_user() -> Generator:
    """Fixture for cleaning up test users after tests"""
    users_to_clean = []

    def _cleanup(username: str):
        users_to_clean.append(username)

    yield _cleanup

    # Cleanup after all tests
    for username in users_to_clean:
        try:
            requests.delete(f"{BASE_URLS['api']}/users/{username}")
            logger.info(f"Cleaned up user: {username}")
        except Exception as e:
            logger.warning(f"Failed to cleanup user {username}: {e}")


@pytest.fixture
def registered_user(unregistered_user, api_url, cleanup_user) -> Dict[str, str]:
    """Register and return a new user"""
    response = requests.post(
        f"{api_url}/auth/register",
        json={
            "username": unregistered_user["username"],
            "password": unregistered_user["password"]
        }
    )
    assert response.status_code == 201, "User registration failed"
    cleanup_user(unregistered_user["username"])
    logger.info(f"Registered new user: {unregistered_user['username']}")
    return unregistered_user


@pytest.fixture
def auth_token(registered_user, auth_url) -> str:
    """Get auth token for registered user"""
    response = requests.post(
        f"{auth_url}/oauth/token",
        data={
            "username": registered_user["username"],
            "password": registered_user["password"],
            "grant_type": "password",
            "client_id": "client",
            "client_secret": "secret"
        }
    )
    token = response.json()["access_token"]
    logger.info(f"Generated auth token for user: {registered_user['username']}")
    return token


# Page object fixtures
@pytest.fixture
def auth_page(page: Page) -> AuthPage:
    """AuthPage instance navigated to login"""
    return AuthPage(page).navigate_to_login()


@pytest.fixture
def registration_page(page: Page) -> RegistrationPage:
    """RegistrationPage instance"""
    return RegistrationPage(page).navigate()


@pytest.fixture
def authenticated_page(auth_page: AuthPage) -> Page:
    """Authenticated page instance"""
    (auth_page
     .fill_credentials(
        username=os.getenv("TEST_USERNAME"),
        password=os.getenv("TEST_PASSWORD")
    )
     .submit_login())

    assert auth_page.check_successful_redirect(), "Login failed"
    logger.info(f"User {os.getenv('TEST_USERNAME')} authenticated successfully")
    return auth_page.page


@pytest.fixture
def profile_page(authenticated_page: Page) -> ProfilePage:
    """ProfilePage instance"""
    profile = ProfilePage(authenticated_page)
    try:
        authenticated_page.goto(
            f"{BASE_URLS['frontend']}/profile",
            timeout=10000,
            wait_until="networkidle"
        )
    except Exception as e:
        pytest.fail(f"Failed to navigate to profile page: {str(e)}")
    return profile


@pytest.fixture
def spending_page(authenticated_page: Page) -> SpendingPage:
    """SpendingPage instance"""
    spending_page = SpendingPage(authenticated_page)
    spending_page.navigate_to_spending()
    return spending_page


# Test data generators
@pytest.fixture
def random_name() -> str:
    """Generate random first name"""
    return fake.first_name()


@pytest.fixture
def random_category() -> str:
    """Generate random category name"""
    return f"{fake.word(part_of_speech='noun')} {fake.word(part_of_speech='noun')}"


@pytest.fixture
def random_amount() -> str:
    """Generate random amount as string"""
    return f"{fake.random_int(100, 9999):04d}"

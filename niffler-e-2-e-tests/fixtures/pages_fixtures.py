import re

import pytest
from playwright.sync_api import Page, expect

from pages.login_page import AuthPage
from pages.profile_page import ProfilePage
from pages.signup_page import RegistrationPage
from pages.spending_page import SpendingPage


@pytest.fixture
def auth_page(page: Page, auth_url, frontend_url):
    return AuthPage(page, auth_url, frontend_url).navigate_to_login()


@pytest.fixture
def authenticated_page(page: Page, auth_url: str, frontend_url: str, settings) -> Page:
    auth_page = AuthPage(page, auth_url, frontend_url)
    auth_page.navigate_to_login()
    auth_page.login(settings.TEST_USERNAME, settings.TEST_PASSWORD)
    expect(page).to_have_url(re.compile(r".*/main"), timeout=10000)
    return page


@pytest.fixture
def logged_in_user(auth_page, valid_user_credentials):
    auth_page.login(valid_user_credentials["username"], valid_user_credentials["password"])
    yield auth_page


@pytest.fixture
def registration_page(page: Page, auth_url: str, frontend_url: str) -> RegistrationPage:
    return RegistrationPage(page, auth_url, frontend_url).navigate()


@pytest.fixture
def profile_page(authenticated_page: Page, frontend_url: str) -> ProfilePage:
    authenticated_page.goto(f"{frontend_url}/profile")
    return ProfilePage(authenticated_page)


@pytest.fixture
def spending_page(authenticated_page: Page) -> SpendingPage:
    """Фикстура для страницы трат"""
    page = SpendingPage(authenticated_page)
    page.navigate_to_spending()
    return page
import os

import pytest
from faker import Faker
from playwright.sync_api import expect
from pydantic import BaseModel

from clients.oauth_client import OauthClient
from conftest import Settings, settings


class UserData(BaseModel):
    username: str
    password: str
    firstname: str | None = None
    surname: str | None = None

@pytest.fixture(scope="session")
def auth_token(settings: Settings):
    return  OauthClient(settings).access_token(settings.TEST_USERNAME, settings.TEST_PASSWORD)

@pytest.fixture
def unregistered_user() -> UserData:
    fake = Faker()
    return UserData(
        username=f"{fake.unique.user_name()}_{os.getpid()}",
        password=fake.password(length=12),
        firstname=fake.first_name(),
        surname=fake.last_name()
    )

@pytest.fixture
def valid_user_credentials(settings) -> dict:
    return {
        "username": settings.TEST_USERNAME,
        "password": settings.TEST_PASSWORD
    }

@pytest.fixture
def invalid_credentials() -> dict:
    return {
        "invalid_password": "invalid_password",
        "nonexistent_user": "non_existent_user@example.com",
        "empty_password": ""
    }

def assert_auth_error(auth_page, expected_error):
    error_text = auth_page.get_error_message()
    assert error_text == expected_error, (
        f"Ожидалась ошибка '{expected_error}'. Получено: '{error_text}'"
    )
    expect(auth_page.page).to_have_url(f"{auth_page.auth_url}/login?error")


@pytest.fixture
def prepared_validation_test(auth_page, valid_user_credentials):
    auth_page.navigate_to_login()
    auth_page.username_input.fill(valid_user_credentials["username"])
    return auth_page

@pytest.fixture(scope="session")
def auth_client(settings: Settings):
    return OauthClient(settings)
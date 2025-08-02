import os
import re

import allure
import pytest
import logging
from typing import Generator, Optional

from allure_commons.reporter import AllureReporter
from pytest import Item, FixtureDef, FixtureRequest
from pydantic_settings import BaseSettings
from pydantic import Field
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, expect
from faker import Faker
from dotenv import load_dotenv
from sqlalchemy import Engine, event

from pages.login_page import AuthPage
from pages.profile_page import ProfilePage
from pages.signup_page import RegistrationPage
from pages.spending_page import SpendingPage



# --------------------------
# 1. Конфигурация и настройки
# --------------------------

class Settings(BaseSettings):
    AUTH_URL: str = Field(default="http://auth.niffler.dc:9000")
    FRONTEND_URL: str = Field(default="http://frontend.niffler.dc")
    GATEWAY_URL: str = Field(default="http://gateway.niffler.dc:8090")
    TEST_USERNAME: str = Field(default="test_user")
    TEST_PASSWORD: str = Field(default="test_password")
    SPEND_DB_URL: str = Field(default="postgresql+psycopg2://postgres:secret@localhost:5432/niffler-spend")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@pytest.fixture(scope="session")
def settings():
    load_dotenv()
    return Settings()


# --------------------------
# 2. Фикстуры URL (производные от настроек)
# --------------------------

@pytest.fixture(scope="session")
def auth_url(settings):
    return settings.AUTH_URL.rstrip('/')


@pytest.fixture(scope="session")
def frontend_url(settings):
    return settings.FRONTEND_URL.rstrip('/')


@pytest.fixture(scope="session")
def gateway_url(settings):
    return settings.GATEWAY_URL.rstrip('/')


# --------------------------
# 3. Инициализация браузера и контекста
# --------------------------

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
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True,
        record_video_dir="videos" if os.getenv("RECORD_VIDEO") else None
    )
    yield context

    # Обработка артефактов при падении теста
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        try:
            os.makedirs("artifacts", exist_ok=True)
            test_name = request.node.name.replace("/", "_")
            page = context.pages[0]
            page.screenshot(path=f"artifacts/{test_name}.png", full_page=True)
            if page.video:
                page.video.save_as(f"artifacts/{test_name}.webm")
        except Exception as e:
            logging.error(f"Failed to save artifacts: {e}")
    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    page = context.new_page()
    yield page
    page.close()


# --------------------------
# 4. Аутентификация и пользователи
# --------------------------

class UserData(BaseSettings):
    username: str
    password: str
    firstname: str | None = None
    surname: str | None = None


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


# --------------------------
# 5. Page Objects и рабочие фикстуры
# --------------------------

@pytest.fixture
def auth_page(page: Page, auth_url, frontend_url):
    return AuthPage(page, auth_url, frontend_url).navigate_to_login()


@pytest.fixture(scope="session")
def auth_context(browser: Browser, auth_url: str, frontend_url: str, settings) -> Generator[BrowserContext, None, None]:
    context = browser.new_context()
    page = context.new_page()
    auth_page = AuthPage(page, auth_url, frontend_url)
    auth_page.navigate_to_login()
    auth_page.login(settings.TEST_USERNAME, settings.TEST_PASSWORD)
    yield context
    context.close()


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


# --------------------------
# 6. Тестовые данные
# --------------------------

@pytest.fixture
def random_category() -> str:
    fake = Faker()
    return f"{fake.word(part_of_speech='noun')} {fake.word(part_of_speech='noun')}"


@pytest.fixture
def random_amount() -> int:
    return Faker().random_int(100, 9999)


@pytest.fixture
def new_spending_data(random_category: str, random_amount: int) -> dict:
    return {
        "amount": str(random_amount),
        "category": random_category,
    }


@pytest.fixture
def fake_name() -> str:
    return Faker().first_name()


# --------------------------
# 7. Хелперы и утилиты
# --------------------------

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


# --------------------------
# 8. Хуки и обработчики
# --------------------------

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def allure_logger(config) -> Optional[AllureReporter]:
    """Безопасное получение Allure логгера"""
    try:
        listener = config.pluginmanager.get_plugin("allure_listener")
        if hasattr(listener, 'allure_logger'):
            return listener.allure_logger
        return None
    except Exception as e:
        pytest.exit(f"Failed to get Allure logger: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_call(item: Item):
    """Динамическое формирование заголовка теста из имени"""
    yield
    try:
        # Преобразуем test_some_feature -> "Some Feature"
        test_name = " ".join(item.name.split("_")[1:]).title()
        allure.dynamic.title(test_name)
    except Exception as e:
        print(f"Error setting dynamic title: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_fixture_setup(fixturedef: FixtureDef, request: FixtureRequest):
    """Форматирование имен фикстур для Allure"""
    yield
    try:
        logger = allure_logger(request.config)
        if logger and hasattr(logger, 'get_last_item'):
            item = logger.get_last_item()

            # Маппинг scope к буквам
            scope_map = {
                'function': 'F',
                'class': 'C',
                'module': 'M',
                'package': 'P',
                'session': 'S'
            }
            scope_letter = scope_map.get(fixturedef.scope, fixturedef.scope[0].upper())

            # Форматирование имени: some_fixture -> "Some Fixture"
            fixture_name = " ".join(fixturedef.argname.split("_")).title()
            item.name = f"[{scope_letter}] {fixture_name}"
    except Exception as e:
        print(f"Error in fixture setup hook: {e}")


sql_queries = []

@event.listens_for(Engine, "before_cursor_execute")
def log_sql(conn, cursor, statement, parameters, context, executemany):
    sql_queries.append(f"SQL: {statement}\nParams: {parameters}")

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item):
    yield
    if hasattr(item, "rep_call") and item.rep_call.failed:
        # Прикрепляем SQL-логи только если они есть
        if sql_queries:
            allure.attach(
                "\n".join(sql_queries),
                name="SQL Queries",
                attachment_type=allure.attachment_type.TEXT
            )
        sql_queries.clear()
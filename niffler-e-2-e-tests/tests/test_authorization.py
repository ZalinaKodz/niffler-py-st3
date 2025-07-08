import os
from playwright.sync_api import expect
from dotenv import load_dotenv
from pages.login_page import AuthPage

load_dotenv()


def test_successful_login(page):
    """Тест успешной авторизации с проверкой конечного URL /main"""
    auth_page = AuthPage(page)
    auth_page.navigate_to_login()

    auth_page.fill_credentials(
        username=os.getenv("TEST_USERNAME"),
        password=os.getenv("TEST_PASSWORD")
    ).submit_login()

    assert auth_page.check_successful_redirect(), (
        f"После входа должен быть переход на {auth_page.frontend_url}/main\n"
        f"Текущий URL: {page.url}"
    )
    expect(page).to_have_url(f"{auth_page.frontend_url}/main")


def test_invalid_password(page):
    """Тест неверного пароля с проверкой URL и сообщения об ошибке"""
    auth_page = AuthPage(page)
    auth_page.navigate_to_login()

    auth_page.fill_credentials(
        username=os.getenv("TEST_USERNAME"),
        password="неверный_пароль"
    ).submit_login()

    assert auth_page.check_error_message(), (
        "Должно быть сообщение 'Неверные учетные данные пользователя'\n"
        f"Найдено: {auth_page.error_message.text_content() if auth_page.error_message.is_visible() else 'Сообщение не найдено'}"
    )


def test_empty_password(page):
    """Тест пустого пароля"""
    auth_page = AuthPage(page)
    auth_page.navigate_to_login()

    auth_page.fill_credentials(
        username=os.getenv("TEST_USERNAME"),
        password=""
    ).submit_login()

    assert auth_page.check_validation_message(), "Должна быть валидация браузера 'Заполните это поле'"

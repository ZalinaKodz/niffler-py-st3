import re

from playwright.sync_api import expect
from dotenv import load_dotenv

from conftest import assert_auth_error

load_dotenv()


def test_successful_login(auth_page, valid_user_credentials):
    """Тест успешной авторизации"""
    auth_page.login(valid_user_credentials["username"], valid_user_credentials["password"])

    assert auth_page.is_logged_in(), (
        f"Ожидался редирект после входа\n"
        f"Текущий URL: {auth_page.page.url}\n"
        f"Сообщение об ошибке: {auth_page.get_error_message() or 'Нет сообщения'}"
    )

def test_invalid_password(auth_page, valid_user_credentials, invalid_credentials):
    """Тест неверного пароля"""
    auth_page.login(valid_user_credentials["username"], invalid_credentials["invalid_password"])
    assert_auth_error(auth_page, "Неверные учетные данные пользователя")

def test_nonexistent_user(auth_page, invalid_credentials):
    """Тест несуществующего пользователя"""
    auth_page.login(invalid_credentials["nonexistent_user"], "any_password")
    assert_auth_error(auth_page, "Неверные учетные данные пользователя")

def test_empty_password(prepared_validation_test, auth_page):
    """Тест валидации пустого пароля"""
    auth_page = prepared_validation_test
    validation_message = auth_page.password_input.evaluate("el => el.validationMessage")
    assert validation_message, "Не сработала валидация пустого пароля"
    assert "Заполните это поле" in validation_message, (
        f"Ожидалась валидация поля. Получено: {validation_message}"
    )

def test_logout(logged_in_user, auth_page):
    """Тест выхода из системы"""
    auth_page = logged_in_user
    auth_page.open_user_menu()
    auth_page.select_sign_out()
    auth_page.confirm_logout()

    expect(auth_page.page).to_have_url(re.compile(r".*/login"))
    expect(auth_page.login_button).to_be_visible()
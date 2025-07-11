import re

from playwright.sync_api import expect
import os
from dotenv import load_dotenv

load_dotenv()


def test_successful_login(auth_page):
    """Тест успешной авторизации"""
    test_username = os.getenv("TEST_USERNAME")
    test_password = os.getenv("TEST_PASSWORD")

    auth_page.login(test_username, test_password)

    assert auth_page.is_logged_in(), (
        f"Ожидался редирект после входа\n"
        f"Текущий URL: {auth_page.page.url}\n"
        f"Сообщение об ошибке: {auth_page.get_error_message() or 'Нет сообщения'}"
    )


def test_invalid_password(auth_page):
    """Тест неверного пароля"""
    test_username = os.getenv("TEST_USERNAME")

    auth_page.login(test_username, "invalid_password")

    error_text = auth_page.get_error_message()
    assert error_text == "Неверные учетные данные пользователя", (
        f"Ожидалась другая ошибка. Получено: {error_text}"
    )
    expect(auth_page.page).to_have_url(f"{auth_page.auth_url}/login?error")


def test_empty_password(auth_page):
    """Тест валидации пустого пароля"""
    test_username = os.getenv("TEST_USERNAME")

    auth_page.navigate_to_login()
    auth_page.username_input.fill(test_username)

    # Проверка HTML5 валидации
    validation_message = auth_page.password_input.evaluate("el => el.validationMessage")
    assert validation_message, "Не сработала валидация пустого пароля"
    assert "Заполните это поле" in validation_message, (
        f"Ожидалась валидация поля. Получено: {validation_message}"
    )


def test_logout(auth_page):
    auth_page.login(os.getenv("TEST_USERNAME"), os.getenv("TEST_PASSWORD"))
    auth_page.open_user_menu()
    auth_page.select_sign_out()
    auth_page.confirm_logout()

    expect(auth_page.page).to_have_url(re.compile(r".*/login"))
    expect(auth_page.login_button).to_be_visible()
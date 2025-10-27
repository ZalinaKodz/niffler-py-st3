import re

import allure
import pytest
from playwright.sync_api import expect
from dotenv import load_dotenv

from fixtures.auth_fixtures import assert_auth_error

load_dotenv()


@allure.epic("Authentication")
@allure.feature("Login Flow")
@pytest.mark.ui
class TestAuthentication:
    @allure.story("Successful Authentication")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_successful_login(self, auth_page, valid_user_credentials):
        """Тест успешной авторизации"""
        with allure.step("Enter valid credentials"):
            auth_page.login(
                username=valid_user_credentials["username"],
                password=valid_user_credentials["password"]
            )

        with allure.step("Verify successful login"):
            assert auth_page.is_logged_in(), (
                f"Expected redirect after login\n"
                f"Current URL: {auth_page.page.url}\n"
                f"Error message: {auth_page.get_error_message() or 'None'}"
            )
            allure.attach(
                auth_page.page.screenshot(),
                name="After successful login",
                attachment_type=allure.attachment_type.PNG
            )

    @allure.story("Failed Authentication")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_invalid_password(self, auth_page, valid_user_credentials, invalid_credentials):
        """Тест неверного пароля"""
        with allure.step("Enter valid username and invalid password"):
            auth_page.login(
                username=valid_user_credentials["username"],
                password=invalid_credentials["invalid_password"]
            )

        with allure.step("Verify authentication error"):
            assert_auth_error(auth_page, "Неверные учетные данные пользователя")
            allure.attach(
                auth_page.page.screenshot(),
                name="Invalid password error",
                attachment_type=allure.attachment_type.PNG
            )

    @allure.story("Failed Authentication")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_nonexistent_user(self, auth_page, invalid_credentials):
        """Тест несуществующего пользователя"""
        with allure.step("Enter nonexistent username"):
            auth_page.login(
                username=invalid_credentials["nonexistent_user"],
                password="any_password"
            )

        with allure.step("Verify authentication error"):
            assert_auth_error(auth_page, "Неверные учетные данные пользователя")
            allure.attach(
                auth_page.get_error_message(),
                name="Error message",
                attachment_type=allure.attachment_type.TEXT
            )

    @allure.story("Form Validation")
    @allure.severity(allure.severity_level.NORMAL)
    def test_empty_password(self, prepared_validation_test, auth_page):
        """Тест валидации пустого пароля"""
        auth_page = prepared_validation_test

        with allure.step("Check password field validation"):
            validation_message = auth_page.password_input.evaluate("el => el.validationMessage")
            allure.attach(
                validation_message,
                name="Validation message",
                attachment_type=allure.attachment_type.TEXT
            )

            assert validation_message, "Password field validation failed"
            assert "Заполните это поле" in validation_message, (
                f"Expected field validation. Got: {validation_message}"
            )

    @allure.story("Logout")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logout(self, logged_in_user, auth_page):
        """Тест выхода из системы"""
        auth_page = logged_in_user

        with allure.step("Open user menu"):
            auth_page.open_user_menu()
            allure.attach(
                auth_page.page.screenshot(),
                name="User menu opened",
                attachment_type=allure.attachment_type.PNG
            )

        with allure.step("Select logout option"):
            auth_page.select_sign_out()

        with allure.step("Confirm logout"):
            auth_page.confirm_logout()

        with allure.step("Verify successful logout"):
            expect(auth_page.page).to_have_url(re.compile(r".*/login"))
            expect(auth_page.login_button).to_be_visible()
            allure.attach(
                auth_page.page.screenshot(),
                name="Login page after logout",
                attachment_type=allure.attachment_type.PNG
            )
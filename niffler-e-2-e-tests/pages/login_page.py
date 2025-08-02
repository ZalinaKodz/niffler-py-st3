from typing import Optional

import allure
from playwright.sync_api import Page
from dotenv import load_dotenv
from pages.base_page import BasePage
load_dotenv()


class AuthPage(BasePage):
    def __init__(self, page: Page, auth_url: str, frontend_url: str):
        super().__init__(page, auth_url, frontend_url)
        self._init_locators()

    @allure.step("Initialize page locators")
    def _init_locators(self):
        """Инициализация локаторов с Allure-шагами"""
        self.username_input = self.page.get_by_role("textbox", name="Username")
        self.password_input = self.page.get_by_role("textbox", name="Password", exact=True)
        self.login_button = self.page.get_by_role("button", name="Log in")
        self.error_message = self.page.locator("p.form__error")

    @allure.step("Navigate to login page")
    def navigate_to_login(self) -> 'AuthPage':
        """Открытие страницы логина с прикреплением скриншота"""
        self.page.goto(f"{self.auth_url}/login", wait_until="networkidle")
        allure.attach(
            self.page.screenshot(),
            name="Login page",
            attachment_type=allure.attachment_type.PNG
        )
        return self

    @allure.step("Fill credentials: username '{username}'")
    def fill_credentials(self, username: str, password: str) -> 'AuthPage':
        """Заполнение полей ввода с логированием"""
        with allure.step(f"Enter username: {username}"):
            self.username_input.fill(username)

        with allure.step("Enter password: ***"):  # Маскируем пароль в логах
            self.password_input.fill(password)
            allure.attach(
                f"Entered password length: {len(password)} characters",
                name="Password info",
                attachment_type=allure.attachment_type.TEXT
            )

        return self

    @allure.step("Submit login form")
    def submit_login(self) -> 'AuthPage':
        """Отправка формы с обработкой навигации"""
        self.login_button.click()
        self.page.wait_for_load_state("networkidle")
        return self

    @allure.step("Perform login as '{username}'")
    def login(self, username: str, password: str) -> 'AuthPage':
        """
        Комбинированный метод входа с полным логированием
        Args:
            username: Логин пользователя
            password: Пароль (будет замаскирован в отчёте)
        """
        self.navigate_to_login()
        self.fill_credentials(username, password)
        with allure.step("Submit credentials"):
            self.submit_login()
            allure.attach(
                self.page.screenshot(),
                name="After login attempt",
                attachment_type=allure.attachment_type.PNG
            )
        return self

    @allure.step("Check if user is logged in")
    def is_logged_in(self, timeout: int = 15000) -> bool:
        """
        Проверка успешного входа с прикреплением текущего URL
        Args:
            timeout: Таймаут ожидания в ms
        """
        current_url = self.page.url
        try:
            self.page.wait_for_url(
                lambda url: "/main" in url or "/dashboard" in url,
                timeout=timeout
            )
            allure.attach(
                f"Successfully logged in. Current URL: {self.page.url}",
                name="Login status",
                attachment_type=allure.attachment_type.TEXT
            )
            return True
        except Exception as e:
            allure.attach(
                f"Login failed. Current URL: {current_url}\nError: {str(e)}",
                name="Login error",
                attachment_type=allure.attachment_type.TEXT
            )
            return False

    @allure.step("Get error message if visible")
    def get_error_message(self) -> Optional[str]:
        """Получение ошибки с прикреплением скриншота"""
        if self.error_message.is_visible():
            message = self.error_message.text_content()
            allure.attach(
                self.page.screenshot(),
                name="Error message visible",
                attachment_type=allure.attachment_type.PNG
            )
            return message
        return None

    @allure.step("Open user menu")
    def open_user_menu(self) -> None:
        """Открытие меню пользователя с логированием"""
        self.page.get_by_role("button", name="Menu").click()
        allure.attach(
            self.page.screenshot(),
            name="User menu opened",
            attachment_type=allure.attachment_type.PNG
        )

    @allure.step("Select sign out option")
    def select_sign_out(self) -> None:
        """Выбор выхода из системы"""
        self.page.get_by_role("menuitem", name="Sign out").click()

    @allure.step("Confirm logout")
    def confirm_logout(self) -> None:
        """Подтверждение выхода с проверкой"""
        self.page.get_by_role("button", name="Log out").click()
        self.page.wait_for_load_state("networkidle")
        allure.attach(
            self.page.screenshot(),
            name="After logout",
            attachment_type=allure.attachment_type.PNG
        )
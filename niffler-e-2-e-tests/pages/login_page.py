from playwright.sync_api import Page
import os
from dotenv import load_dotenv

load_dotenv()

class AuthPage:
    def __init__(self, page: Page):
        self.page = page
        self.auth_url = os.getenv("AUTH_URL", "http://auth.niffler.dc:9000").rstrip('/')
        self.frontend_url = os.getenv("FRONTEND_URL", "http://frontend.niffler.dc").rstrip('/')

        # Локаторы
        self.username_input = page.get_by_role("textbox", name="Username")
        self.password_input = page.get_by_role("textbox", name="Password", exact=True)
        self.login_button = page.get_by_role("button", name="Log in")
        self.error_message = page.locator("p.form__error")

    def navigate_to_login(self):
        self.page.goto(f"{self.auth_url}/login", wait_until="networkidle")
        return self

    def fill_credentials(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        return self

    def submit_login(self):
        self.login_button.click()
        return self

    def login(self, username: str, password: str):
        """Комбинированный метод для быстрого входа"""
        self.navigate_to_login()
        self.fill_credentials(username, password)
        self.submit_login()
        return self

    def is_logged_in(self, timeout=15000):
        """Проверка успешного входа по URL"""
        try:
            self.page.wait_for_url(
                lambda url: "/main" in url or "/dashboard" in url,
                timeout=timeout
            )
            return True
        except:
            return False

    def get_error_message(self):
        """Получение текста ошибки"""
        if self.error_message.is_visible():
            return self.error_message.text_content()
        return None

    def open_user_menu(self):
        self.page.get_by_role("button", name="Menu").click()

    def select_sign_out(self):
        self.page.get_by_role("menuitem", name="Sign out").click()

    def confirm_logout(self):
        self.page.get_by_role("button", name="Log out").click()
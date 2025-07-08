from playwright.async_api import expect
from playwright.sync_api import Page
import os
from dotenv import load_dotenv

load_dotenv()


class AuthPage:
    def __init__(self, page: Page):
        self.page = page
        self.auth_url = os.getenv("AUTH_URL").rstrip('/')
        self.frontend_url = os.getenv("FRONTEND_URL").rstrip('/')

        # Locators
        self.username_input = page.get_by_role("textbox", name="Username")
        self.password_input = page.get_by_role("textbox", name="Password", exact=True)
        self.login_button = page.get_by_role("button", name="Log in")

        # More robust error message locator that matches your application
        self.error_message = page.locator(
            "[data-testid='error-message'], .error-text, .alert-error, [class*='error']"
        )

    def navigate_to_login(self):
        self.page.goto(f"{self.auth_url}/login", wait_until="domcontentloaded")
        return self

    def fill_credentials(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        return self

    def submit_login(self):
        self.login_button.click()
        return self

    def check_successful_redirect(self, timeout=40000):
        try:
            self.page.wait_for_url(
                lambda url: url.startswith(f"{self.frontend_url}/main") or
                            "/authorized?code=" in url,
                timeout=timeout
            )
            if "/authorized?code=" in self.page.url:
                self.page.wait_for_url(f"{self.frontend_url}/main", timeout=timeout)
            return True
        except:
            return False

    def check_error_redirect(self, timeout=10000):
        try:
            self.page.wait_for_url(
                f"{self.auth_url}/login?error",
                timeout=timeout,
                wait_until="load"
            )
            return True
        except:
            return False

    def check_error_message(self, expected_text="Неверные учетные данные пользователя", timeout=15000):
        try:
            # Ищем элемент с точным текстом ошибки
            error_element = self.page.get_by_text(expected_text, exact=True)
            error_element.wait_for(state="visible", timeout=timeout)
            return True
        except Exception as e:
            print(f"Ошибка при поиске сообщения: {e}\nТекущий URL: {self.page.url}")
            # Дополнительная проверка: есть ли текст ошибки где-то на странице
            if expected_text in self.page.content():
                print("Текст ошибки найден в содержимом страницы, но не в видимом элементе")
            return False

    def test_invalid_password(auth_page):
        """Тест неверного пароля с проверкой URL и текста ошибки"""
        (auth_page
         .fill_credentials(
            username=os.getenv("TEST_USERNAME"),
            password="неверный_пароль"
        )
         .submit_login())

        # Проверяем точное соответствие текста ошибки
        assert auth_page.check_error_message(), (
            f"Должно быть сообщение 'Неверные учетные данные пользователя'\n"
            f"Содержимое страницы: {auth_page.page.text_content()}"
        )


    def check_validation_message(self, field="password"):
        try:
            if field == "password":
                return "Заполните это поле" in self.password_input.evaluate("el => el.validationMessage")
            return "Заполните это поле" in self.username_input.evaluate("el => el.validationMessage")
        except:
            return False

    def logout(self) -> None:
        """Выполняет выход из системы"""
        self.page.get_by_role("button", name="Menu").click()
        self.page.get_by_role("menuitem", name="Sign out").click()
        self.page.get_by_role("button", name="Log out").click()
        self.page.wait_for_url(f"{self.auth_url}/login")

    def verify_logout_successful(self):
        """Verify successful logout by checking login button visibility and URL"""
        expect(self.page.get_by_role("button", name="Log in")).to_be_visible()
        expect(self.page).to_have_url(f"{self.auth_url}/login")

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username_field = page.get_by_role("textbox", name="Username")
        self.password_field = page.get_by_role("textbox", name="Password")
        self.login_button = page.get_by_role("button", name="Log in")

    def login(self, username: str, password: str):
        self.username_field.fill(username)
        self.password_field.fill(password)
        self.login_button.click()

    def verify_logout_successful(self) -> None:
        """Проверяет успешный выход из системы"""
        expect(self.page.get_by_role("button", name="Log in")).to_be_visible()
        expect(self.page).to_have_url(f"{self.auth_url}/login")

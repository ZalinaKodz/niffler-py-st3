from playwright.sync_api import Page
from pages.base_page import BasePage


class RegistrationPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Уникальные локаторы для регистрации
        self.confirm_password_input = page.get_by_role("textbox", name="Submit password")
        self.sign_up_button = page.get_by_role("button", name="Sign Up")
        self.success_message = page.get_by_text("Congratulations! You've registered!", exact=False)

    def navigate(self):
        self.page.goto(f"{self.auth_url}/register", wait_until="domcontentloaded")
        return self

    def fill_registration_form(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.confirm_password_input.fill(password)
        return self

    def submit_form(self):
        self.sign_up_button.wait_for(state="visible")
        self.sign_up_button.click()
        return self

    def is_success_message_visible(self, timeout=10000):
        self.success_message.wait_for(state="visible", timeout=timeout)
        return self.success_message.is_visible()
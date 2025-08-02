import allure
from playwright.sync_api import Page
from pages.base_page import BasePage


class RegistrationPage(BasePage):
    def __init__(self, page: Page, auth_url: str, frontend_url: str):
        super().__init__(page, auth_url, frontend_url)
        self.confirm_password_input = page.get_by_role("textbox", name="Submit password")
        self.sign_up_button = page.get_by_role("button", name="Sign Up")
        self.success_message = page.get_by_text("Congratulations! You've registered!", exact=False)

    @allure.step("Navigate to registration page")
    def navigate(self) -> 'RegistrationPage':
        """Navigate to registration page and wait for DOM content loaded."""
        with allure.step(f"Opening registration page at {self.auth_url}/register"):
            self.page.goto(f"{self.auth_url}/register", wait_until="domcontentloaded")
            self._attach_page_screenshot("Registration page loaded")
        return self

    @allure.step("Fill registration form")
    def fill_registration_form(self, username: str, password: str) -> 'RegistrationPage':
        """Fill registration form with provided credentials."""
        with allure.step(f"Filling form with username: {username}"):
            self.username_input.fill(username)
            self._attach_field_value("Username", username)

        with allure.step("Filling password fields"):
            self.password_input.fill(password)
            self.confirm_password_input.fill(password)
            self._attach_field_value("Password", "***")  # Mask sensitive data

        self._attach_page_screenshot("Form filled")
        return self

    @allure.step("Submit registration form")
    def submit_form(self) -> 'RegistrationPage':
        """Submit the registration form."""
        self.sign_up_button.wait_for(state="visible")
        with allure.step("Clicking Sign Up button"):
            self.sign_up_button.click()
            self._attach_page_screenshot("After form submission")
        return self

    @allure.step("Check if success message is visible")
    def is_success_message_visible(self, timeout: int = 10000) -> bool:
        """Check if registration success message is visible."""
        self.success_message.wait_for(state="visible", timeout=timeout)
        is_visible = self.success_message.is_visible()
        self._attach_page_screenshot("Success message check")
        return is_visible

    def _attach_page_screenshot(self, name: str) -> None:
        """Attach page screenshot to Allure report."""
        allure.attach(
            self.page.screenshot(),
            name=name,
            attachment_type=allure.attachment_type.PNG
        )

    def _attach_field_value(self, field_name: str, value: str) -> None:
        """Attach field value to Allure report."""
        allure.attach(
            f"{field_name}: {value}",
            name=f"{field_name} value",
            attachment_type=allure.attachment_type.TEXT
        )
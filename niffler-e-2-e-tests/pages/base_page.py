from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page, auth_url: str, frontend_url: str):
        self.page = page
        self.auth_url = auth_url
        self.frontend_url = frontend_url

        # Общие локаторы для авторизации
        self.username_input = page.get_by_role("textbox", name="Username")
        self.password_input = page.get_by_role("textbox", name="Password", exact=True)
        self.login_button = page.get_by_role("button", name="Log in")
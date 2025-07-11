from playwright.sync_api import Page
import os
from dotenv import load_dotenv

load_dotenv()


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.auth_url = os.getenv("AUTH_URL").rstrip('/')

        # Общие локаторы для авторизации
        self.username_input = page.get_by_role("textbox", name="Username")
        self.password_input = page.get_by_role("textbox", name="Password", exact=True)
        self.login_button = page.get_by_role("button", name="Log in")
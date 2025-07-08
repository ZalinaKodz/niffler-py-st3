from dotenv import load_dotenv
from pages.signup_page import RegistrationPage
from playwright.sync_api import expect
from utils.create_user import UserDataFactory

load_dotenv()

def test_user_registration(page):
    """Test user registration with success message verification"""
    # Подготовка
    registration_page = RegistrationPage(page)
    registration_page.navigate()
    user_data = UserDataFactory.generate_valid_user()

    # Действия
    registration_page \
        .fill_registration_form(user_data["username"], user_data["password"]) \
        .submit_form()

    # Проверки
    assert registration_page.is_success_message_visible(), \
        "Success message should be visible after registration"
    expect(registration_page.success_message).to_be_visible()

import os
from playwright.sync_api import expect
from dotenv import load_dotenv
from faker import Faker
from pages.login_page import LoginPage, AuthPage
from pages.spending_page import SpendingPage
from pages.profile_page import ProfilePage
import time

load_dotenv()
fake = Faker()


# Вспомогательные функции
def _login(page):
    """Выполняет авторизацию пользователя"""
    login_page = LoginPage(page)
    login_page.page.goto(f"{os.getenv('AUTH_URL')}/login")
    login_page.login(
        username=os.getenv("TEST_USERNAME"),
        password=os.getenv("TEST_PASSWORD")
    )
    return page


def _add_test_spending(page, amount="0500", category="books"):
    """Добавляет тестовую трату и возвращает количество трат после добавления"""
    spending_page = SpendingPage(page)
    spending_page.navigate_to_spending()
    spending_page.add_spending(amount=amount, category=category)
    expect(spending_page.success_message).to_be_visible()
    return spending_page.get_spendings_count()


# Тесты
def test_add_spending_with_category(page):
    """Тест добавления траты с указанием категории"""
    _login(page)
    spending_page = SpendingPage(page)
    spending_page.navigate_to_spending()
    spending_page.add_spending(amount="0300", category="cinema")
    expect(spending_page.success_message).to_be_visible()


def test_add_spending_without_category(page):
    """Тест добавления траты без категории"""
    _login(page)
    spending_page = SpendingPage(page)
    spending_page.navigate_to_spending()
    spending_page.add_spending(amount="0200")
    expect(spending_page.error_message).to_be_visible()


def test_profile_name_update(page):
    """Тест обновления имени профиля"""
    _login(page)
    random_name = fake.first_name()
    profile_page = ProfilePage(page)
    profile_page.navigate_to_profile()
    profile_page.update_profile_name(random_name)

    expect(profile_page.name_field).to_have_value(random_name)
    expect(profile_page.success_message).to_be_visible()
    page.reload()
    expect(profile_page.name_field).to_have_value(random_name)


def test_user_logout(page):
    """Тест выхода пользователя из системы"""
    _login(page)
    auth_page = AuthPage(page)
    auth_page.logout()

    expect(page.get_by_role("button", name="Log in")).to_be_visible()
    expect(page).to_have_url(f"{os.getenv('AUTH_URL')}/login")